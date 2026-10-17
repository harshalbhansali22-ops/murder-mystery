"""Case loader and schema validator for MurderBox."""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from murderbox.models.case import CaseData, SuspectProfile, EvidenceItem, Location, TimelineEvent


class CaseLoader:
    """Loads, validates, and manages access to case mystery files."""

    def __init__(self, case_path: Optional[str] = None):
        if case_path is None:
            # Default to the bundled case in data/cases/the_vance_mystery.json
            base_dir = Path(__file__).resolve().parent.parent.parent
            case_path = str(base_dir / "data" / "cases" / "the_vance_mystery.json")
        self.case_path = Path(case_path)
        self.case_data: CaseData = self._load_and_validate()

    def _load_and_validate(self) -> CaseData:
        """Reads JSON and validates against Pydantic CaseData schema."""
        if not self.case_path.exists():
            raise FileNotFoundError(f"Case file not found at: {self.case_path}")

        with open(self.case_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        case = CaseData.model_validate(raw_data)
        self._verify_case_integrity(case)
        return case

    def _verify_case_integrity(self, case: CaseData) -> None:
        """Ensures cross-referential integrity across suspects, clues, and locations."""
        suspect_ids = {s.id for s in case.suspects}
        evidence_ids = {e.id for e in case.evidence}
        location_ids = {loc.id for loc in case.locations}

        # Verify culprit
        if case.solution.culprit_id not in suspect_ids:
            raise ValueError(f"Culprit ID '{case.solution.culprit_id}' not found among suspects.")

        culprit_profile = case.get_suspect(case.solution.culprit_id)
        if culprit_profile and not culprit_profile.is_culprit:
            raise ValueError(f"Culprit '{case.solution.culprit_id}' does not have is_culprit=True.")

        # Verify key evidence IDs
        for key_ev in case.solution.key_evidence_ids:
            if key_ev not in evidence_ids:
                raise ValueError(f"Key evidence '{key_ev}' not defined in evidence list.")

        # Verify evidence location bindings
        for ev in case.evidence:
            if ev.location_id not in location_ids:
                raise ValueError(f"Evidence '{ev.id}' assigned to unknown location '{ev.location_id}'.")

        # Verify location evidence IDs
        for loc in case.locations:
            for ev_id in loc.evidence_ids:
                if ev_id not in evidence_ids:
                    raise ValueError(f"Location '{loc.id}' references unknown evidence '{ev_id}'.")

        # Verify timeline suspect references
        for event in case.timeline:
            for s_id in event.involved_suspect_ids:
                if s_id not in suspect_ids:
                    raise ValueError(f"Timeline event at {event.time_str} references unknown suspect '{s_id}'.")

    def get_case(self) -> CaseData:
        return self.case_data

    def get_suspect(self, suspect_id: str) -> Optional[SuspectProfile]:
        return self.case_data.get_suspect(suspect_id)

    def get_evidence(self, evidence_id: str) -> Optional[EvidenceItem]:
        return self.case_data.get_evidence(evidence_id)

    def get_location(self, location_id: str) -> Optional[Location]:
        return self.case_data.get_location(location_id)

    def get_evidence_for_location(self, location_id: str) -> List[EvidenceItem]:
        loc = self.get_location(location_id)
        if not loc:
            return []
        return [e for e in self.case_data.evidence if e.id in loc.evidence_ids]
