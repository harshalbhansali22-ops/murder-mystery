"""Models for interrogation dialogues, statements, claims, and contradiction results."""

from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import time


class ContradictionType(str, Enum):
    SELF_CONTRADICTION = "self_contradiction"
    EVIDENCE_CONTRADICTION = "evidence_contradiction"
    INTER_SUSPECT_CONFLICT = "inter_suspect_conflict"
    GROUND_TRUTH_CONFLICT = "ground_truth_conflict"


class ContradictionSeverity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class StatementClaim(BaseModel):
    """An atomic factual claim extracted from suspect speech."""
    claim_id: str
    suspect_id: str
    turn_id: str
    text: str
    entity: Optional[str] = None
    claimed_time: Optional[str] = None
    claimed_location: Optional[str] = None
    claim_type: str = Field(default="alibi", description="alibi, action, relationship, denial, accusation")
    verified: Optional[bool] = None
    is_contradiction: bool = False


class ContradictionResult(BaseModel):
    """Details of a detected contradiction."""
    type: ContradictionType
    severity: ContradictionSeverity = ContradictionSeverity.HIGH
    description: str
    suspect_id: str
    claim_text: str
    conflicting_source: str
    conflicting_detail: str
    timestamp: float = Field(default_factory=time.time)


class InterrogationTurn(BaseModel):
    """A single turn of interrogation between the player and an AI suspect."""
    turn_id: str
    suspect_id: str
    question: str
    presented_evidence_ids: List[str] = Field(default_factory=list)
    response: str
    claims: List[StatementClaim] = Field(default_factory=list)
    contradictions_found: List[ContradictionResult] = Field(default_factory=list)
    timestamp: float = Field(default_factory=time.time)
    model_name: Optional[str] = None
    is_fallback: bool = False
