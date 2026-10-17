"""Models for game state, player progression, accusations, and scoring."""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import time
from murderbox.models.dialogue import InterrogationTurn, ContradictionResult


class AccusationSubmission(BaseModel):
    """The player's final accusation package."""
    accused_suspect_id: str
    selected_motive: str
    selected_evidence_ids: List[str] = Field(default_factory=list)
    closing_rationale: str


class AccusationResult(BaseModel):
    """Evaluation result of the player's accusation."""
    is_culprit_correct: bool
    culprit_score: int = 0          # max 40
    motive_score: int = 0           # max 25
    evidence_score: int = 0         # max 25
    contradiction_bonus: int = 0    # max 10
    total_score: int = 0            # max 100
    rank_title: str = "Wrongful Arrest"
    score_percentage: float = 0.0
    breakdown: Dict[str, Any] = Field(default_factory=dict)
    narrative_verdict: str = ""
    culprit_confession: str = ""


class InvestigationState(BaseModel):
    """Deterministic state of the player's ongoing case."""
    case_id: str
    current_turn: int = 0
    max_turns: int = 40
    discovered_evidence_ids: List[str] = Field(default_factory=list)
    explored_location_ids: List[str] = Field(default_factory=list)
    interrogation_turns: List[InterrogationTurn] = Field(default_factory=list)
    detected_contradictions: List[ContradictionResult] = Field(default_factory=list)
    notebook_notes: List[str] = Field(default_factory=list)
    is_solved: bool = False
    final_result: Optional[AccusationResult] = None
    started_at: float = Field(default_factory=time.time)

    def is_game_over(self) -> bool:
        return self.is_solved or self.current_turn >= self.max_turns
