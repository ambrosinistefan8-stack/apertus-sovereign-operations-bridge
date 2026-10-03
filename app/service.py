from __future__ import annotations
import hashlib,json,time
from dataclasses import asdict
from .apertus_client import ApertusClient
from .control import evaluate
from .prompt import SYSTEM_PROMPT,build_user_prompt
from .schema import SourceDocument

def run_workflow(client:ApertusClient,task:str,documents:list[SourceDocument],required_fields:list[str])->dict:
    started=time.time()
    output=client.analyze(SYSTEM_PROMPT,build_user_prompt(task,documents,required_fields))
    # A model cannot erase the caller's known requirement for human approval.
    control=evaluate(output,(action for d in documents for action in d.requested_actions))
    evidence_input=json.dumps({"task":task,"documents":[asdict(d) for d in documents],"required_fields":required_fields},ensure_ascii=False,sort_keys=True).encode()
    return {"status":control.status,"task":task,"model_output":output.as_dict(),"control":control.as_dict(),"evidence":{"input_sha256":hashlib.sha256(evidence_input).hexdigest(),"source_count":len(documents),"elapsed_ms":round((time.time()-started)*1000,2),"model_authorized_external_action":False,"transport":getattr(client,"last_metadata",{})}}
