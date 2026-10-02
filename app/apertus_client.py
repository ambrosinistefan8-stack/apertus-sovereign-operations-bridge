from __future__ import annotations
import json, os, urllib.request
from abc import ABC, abstractmethod
from .schema import ModelOutput, Fact

class ApertusClient(ABC):
    @abstractmethod
    def analyze(self, system_prompt:str, user_prompt:str)->ModelOutput: ...

class OpenAICompatibleApertusClient(ApertusClient):
    def __init__(self,base_url=None,api_key=None,model=None):
        self.base_url=(base_url or os.environ.get("APERTUS_BASE_URL","")).rstrip("/")
        self.api_key=api_key or os.environ.get("APERTUS_API_KEY","")
        self.model=model or os.environ.get("APERTUS_MODEL","swiss-ai/Apertus-v1.5-8B")
        if not self.base_url: raise ValueError("APERTUS_BASE_URL is required in live mode.")

    def analyze(self,system_prompt,user_prompt):
        body={"model":self.model,"temperature":0,"messages":[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}]}
        headers={"Content-Type":"application/json"}
        if self.api_key: headers["Authorization"]=f"Bearer {self.api_key}"
        req=urllib.request.Request(f"{self.base_url}/chat/completions",data=json.dumps(body).encode(),headers=headers,method="POST")
        with urllib.request.urlopen(req,timeout=90) as response:
            payload=json.loads(response.read().decode())
        return ModelOutput.from_dict(self._extract_json(payload["choices"][0]["message"]["content"]))

    @staticmethod
    def _extract_json(content):
        content=content.strip()
        if content.startswith("~~~"): content=content.strip("~")
        if content.startswith("```"):
            lines=content.splitlines()[1:]
            if lines and lines[-1].strip().startswith("```"): lines=lines[:-1]
            content="\n".join(lines)
            if content.lstrip().startswith("json"): content=content.lstrip()[4:].lstrip()
        return json.loads(content)

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
