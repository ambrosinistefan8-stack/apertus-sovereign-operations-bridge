from __future__ import annotations
import json, os, time, urllib.request
from abc import ABC, abstractmethod
from .schema import ModelOutput, Fact

class ApertusClient(ABC):
    @abstractmethod
    def analyze(self, system_prompt:str, user_prompt:str)->ModelOutput: ...

class OpenAICompatibleApertusClient(ApertusClient):
    def __init__(self,base_url=None,api_key=None,model=None,timeout=90,user_agent=None):
        self.base_url=(base_url or os.environ.get("APERTUS_BASE_URL","")).rstrip("/")
        self.api_key=api_key or os.environ.get("APERTUS_API_KEY","")
        self.model=model or os.environ.get("APERTUS_MODEL","swiss-ai/Apertus-v1.5-8B")
        self.timeout=timeout
        self.user_agent=user_agent or os.environ.get("APERTUS_USER_AGENT","SPINNENNETZ-DNA/1.0")
        self.last_metadata={}
        if not self.base_url: raise ValueError("APERTUS_BASE_URL is required in live mode.")

    def analyze(self,system_prompt,user_prompt):
        return ModelOutput.from_dict(self._extract_json(self.complete(system_prompt,user_prompt)))

    def complete(self,system_prompt,user_prompt):
        """One shared HTTP path for connectivity and structured workflow requests."""
        self.last_metadata={}
        started=time.monotonic()
        body={"model":self.model,"temperature":0,"max_tokens":1200,"response_format":{"type":"json_object"},"messages":[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}]}
        headers={"Content-Type":"application/json","User-Agent":self.user_agent}
        if self.api_key: headers["Authorization"]=f"Bearer {self.api_key}"
        req=urllib.request.Request(f"{self.base_url}/chat/completions",data=json.dumps(body).encode(),headers=headers,method="POST")
        with urllib.request.urlopen(req,timeout=self.timeout) as response:
            payload=json.loads(response.read().decode())
            status=getattr(response,"status",None)
        content=payload["choices"][0]["message"]["content"]
        self.last_metadata={"http_status":status,"model_used":payload.get("model"),
            "latency_ms":round((time.monotonic()-started)*1000,2),
            "response_present":isinstance(content,str) and bool(content.strip()),
            **{k:payload.get("usage",{}).get(k) for k in ("prompt_tokens","completion_tokens","total_tokens")}}
        return content

    @staticmethod
    def _extract_json(content):
        """Extract the first complete JSON object from a model reply.

        The prompt requests JSON-only output, but real models may wrap the
        object in Markdown fences or brief prose. Only a syntactically complete
        JSON object is accepted; surrounding text is never executed.
        """
        content=content.strip()
        if content.startswith("~~~"):
            content=content.strip("~").strip()
        if content.startswith("\x60\x60\x60"):
            lines=content.splitlines()[1:]
            if lines and lines[-1].strip().startswith("\x60\x60\x60"):
                lines=lines[:-1]
            content="\n".join(lines).strip()
            if content.lower().startswith("json"):
                content=content[4:].lstrip()

        try:
            parsed=json.loads(content)
            if isinstance(parsed,dict):
                return parsed
        except json.JSONDecodeError as first_error:
            decoder=json.JSONDecoder()
            for pos,char in enumerate(content):
                if char!="{":
                    continue
                try:
                    parsed,end=decoder.raw_decode(content[pos:])
                except json.JSONDecodeError:
                    continue
                if isinstance(parsed,dict):
                    return parsed
            raise first_error
        raise ValueError("Apertus response must contain a JSON object.")

class MockApertusClient(ApertusClient):
    def analyze(self,system_prompt,user_prompt):
        payload=json.loads(user_prompt)
        text="\n".join(d["text"] for d in payload["documents"])
        scenario=self._scenario(text)
        if scenario=="conflict":
            return ModelOutput([Fact("delivery_days","3","policy"),Fact("delivery_days","7","product"),Fact("product","Apertus Office Pack","product")],[],[],"Draft prepared, but delivery timing conflicts across sources.",["draft_response"])
        if scenario=="missing":
            return ModelOutput([Fact("product","Apertus Office Pack","product"),Fact("price_chf","490","product")],["delivery_days"],[],"Draft cannot be finalized without delivery timing.",["draft_response"])
        if scenario=="untrusted":
            return ModelOutput([Fact("product","Apertus Office Pack","product"),Fact("price_chf","490","product")],[],["A source document instructs the AI to ignore rules and send automatically."],"No external action proposed.",["draft_response"])
        if scenario=="human_gate":
            return ModelOutput([Fact("product","Apertus Office Pack","product"),Fact("price_chf","490","product"),Fact("delivery_days","3","policy")],[],[],"Response draft is ready for approval.",["send_email"])
        return ModelOutput([Fact("product","Apertus Office Pack","product"),Fact("price_chf","490","product"),Fact("delivery_days","3","policy"),Fact("support","Email support included","policy")],[],[],"Thank you for your inquiry. The Apertus Office Pack costs CHF 490, includes email support, and is normally delivered within 3 business days.",["draft_response"])

    @staticmethod
    def _scenario(text):
        for name in ("SCENARIO_CONFLICT","SCENARIO_MISSING","SCENARIO_UNTRUSTED","SCENARIO_HUMAN_GATE"):
            if name in text: return name.removeprefix("SCENARIO_").lower()
        return "normal"
