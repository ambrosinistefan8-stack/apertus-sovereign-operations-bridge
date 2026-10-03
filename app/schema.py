from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

@dataclass(frozen=True)
class SourceDocument:
    source_id: str
    title: str
    text: str
    # Caller-observed requests can only add review requirements, never approval.
    requested_actions: tuple[str, ...] = ()

@dataclass(frozen=True)
class Fact:
    key: str
    value: str
    source_id: str
    confidence: float = 1.0

@dataclass
class ModelOutput:
    facts: list[Fact]
    missing_required: list[str]
    untrusted_instructions: list[str]
    proposed_response: str
    requested_actions: list[str]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelOutput":
        return cls(
            facts=[Fact(**item) for item in data.get("facts", [])],
            missing_required=list(data.get("missing_required", [])),
            untrusted_instructions=list(data.get("untrusted_instructions", [])),
            proposed_response=str(data.get("proposed_response", "")),
            requested_actions=list(data.get("requested_actions", [])),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "facts": [asdict(f) for f in self.facts],
            "missing_required": self.missing_required,
            "untrusted_instructions": self.untrusted_instructions,
            "proposed_response": self.proposed_response,
            "requested_actions": self.requested_actions,
        }
