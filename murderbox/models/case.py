"""Pydantic schemas for case data, suspects, evidence, and timeline."""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class KnowledgeBoundaries(BaseModel):
    """Defines what information a character is aware of and forbidden from revealing."""
    allowed_topics: List[str] = Field(default_factory=list, description="Topics suspect can freely speak about.")
    forbidden_topics: List[str] = Field(default_factory=list, description="Secrets or third-party facts suspect must NOT leak.")
    alibi_statement: str = Field(..., description="Default claimed alibi.")
    hidden_secret: str = Field(..., description="Guilty secret unrelated or related to murder.")


class SuspectProfile(BaseModel):
    """Full character profile of a suspect."""
    id: str
    name: str
    role: str
    age: int
    personality: str
    relationship_to_victim: str
    motive: str
    alibi: str
    secret: str
    is_culprit: bool = False
    public_bio: str
    avatar_emoji: str = "👤"
    knowledge_boundaries: KnowledgeBoundaries
    deflection_phrases: List[str] = Field(default_factory=list)
    initial_statement: str = ""
    deception_strategy: Optional[str] = Field(
        None, description="Guidance for the culprit or guilty party on how to deceive."
    )


class EvidenceItem(BaseModel):
    """Forensic, physical, or documentary clue."""
    id: str
    name: str
    location_id: str
    category: str = Field(default="Physical", description="Physical, Forensic, Document, Digital")
    description: str
    detailed_inspection: str
    related_suspect_ids: List[str] = Field(default_factory=list)
    contradiction_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords or claims in suspect testimony that this evidence directly contradicts."
    )
    is_critical: bool = False
    discovered: bool = False


class TimelineEvent(BaseModel):
    """Known or reconstructed chronological event."""
    time_str: str
    description: str
    involved_suspect_ids: List[str] = Field(default_factory=list)
    verified: bool = False
    is_key_time: bool = False


class Location(BaseModel):
    """A searchable area in the crime scene manor."""
    id: str
    name: str
    description: str
    evidence_ids: List[str] = Field(default_factory=list)
    searched: bool = False


class CaseSolution(BaseModel):
    """The authoritative ground truth of the case."""
    culprit_id: str
    motive_summary: str
    method_summary: str
    key_evidence_ids: List[str]
    timeline_reconstruction: List[str]
    confession_text: str


class CaseData(BaseModel):
    """Complete case package structure."""
    case_id: str
    title: str
    subtitle: str
    victim_name: str
    victim_age: int
    victim_bio: str
    incident_time: str
    cause_of_death: str
    synopsis: str
    locations: List[Location]
    suspects: List[SuspectProfile]
    evidence: List[EvidenceItem]
    timeline: List[TimelineEvent]
    solution: CaseSolution

    def get_suspect(self, suspect_id: str) -> Optional[SuspectProfile]:
        for s in self.suspects:
            if s.id == suspect_id:
                return s
        return None

    def get_evidence(self, evidence_id: str) -> Optional[EvidenceItem]:
        for e in self.evidence:
            if e.id == evidence_id:
                return e
        return None

    def get_location(self, location_id: str) -> Optional[Location]:
        for loc in self.locations:
            if loc.id == location_id:
                return loc
        return None
