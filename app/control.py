from __future__ import annotations
from dataclasses import dataclass, asdict
from collections import defaultdict
from .schema import ModelOutput

PROTECTED_ACTIONS={"send_email","send_message","payment","purchase","sign_contract","delete_record","publish_external","change_permissions"}

@dataclass
class ControlResult:
    status:str
    reasons:list[str]
    conflicts:dict[str,list[str]]
    missing_required:list[str]
    protected_actions:list[str]
    untrusted_instructions:list[str]
    def as_dict(self)->dict:
        return asdict(self)

def _normalize(value:str)->str:
    return " ".join(value.lower().strip().split())

def detect_conflicts(model_output:ModelOutput)->dict[str,list[str]]:
    values=defaultdict(set); originals=defaultdict(list)
    for fact in model_output.facts:
        values[fact.key].add(_normalize(fact.value))
        if fact.value not in originals[fact.key]:
            originals[fact.key].append(fact.value)
    return {k:originals[k] for k,v in values.items() if len(v)>1}

def evaluate(model_output:ModelOutput,requested_actions=())->ControlResult:
    conflicts=detect_conflicts(model_output)
    protected=sorted((set(model_output.requested_actions)|set(requested_actions))&PROTECTED_ACTIONS)
    reasons=[]
    if model_output.untrusted_instructions:
        return ControlResult("BLOCKED",["Untrusted instructions detected inside source documents."],conflicts,model_output.missing_required,protected,model_output.untrusted_instructions)
    if conflicts: reasons.append("Conflicting source facts require human resolution.")
    if model_output.missing_required: reasons.append("Required information is missing.")
    if protected: reasons.append("A protected external action requires explicit human approval.")
    if reasons:
        return ControlResult("HUMAN_REVIEW",reasons,conflicts,model_output.missing_required,protected,model_output.untrusted_instructions)
    return ControlResult("VERIFIED",["No deterministic control blocker detected."],{},[],[],[])
