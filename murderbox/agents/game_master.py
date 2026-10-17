"""GameMasterAgent providing detective hints, case progress metrics, and notebook summaries."""

from typing import List, Dict, Optional, Any
from murderbox.models.case import CaseData
from murderbox.models.investigation import InvestigationState


class GameMasterAgent:
    """Provides dynamic guidance, hints, and progression tracking to the detective."""

    def __init__(self, case_data: CaseData):
        self.case_data = case_data

    def get_progress_metrics(self, state: InvestigationState) -> Dict[str, Any]:
        """Calculates current investigation completion statistics."""
        total_evidence = len(self.case_data.evidence)
        discovered_evidence = len(state.discovered_evidence_ids)

        total_locations = len(self.case_data.locations)
        explored_locations = len(state.explored_location_ids)

        interrogated_suspects = len({t.suspect_id for t in state.interrogation_turns})
        total_suspects = len(self.case_data.suspects)

        contradictions_caught = len(state.detected_contradictions)

        score_estimate = int(
            (discovered_evidence / total_evidence) * 40
            + (interrogated_suspects / total_suspects) * 30
            + min(30, contradictions_caught * 10)
        )

        return {
            "evidence_discovered": f"{discovered_evidence}/{total_evidence}",
            "evidence_percent": int((discovered_evidence / total_evidence) * 100) if total_evidence else 0,
            "locations_explored": f"{explored_locations}/{total_locations}",
            "suspects_questioned": f"{interrogated_suspects}/{total_suspects}",
            "contradictions_caught": contradictions_caught,
            "investigation_readiness": min(100, score_estimate),
            "turns_remaining": max(0, state.max_turns - state.current_turn),
        }

    def get_next_lead_hint(self, state: InvestigationState) -> str:
        """Determines the most strategic next step for the player."""
        # 1. Unsearched locations
        unsearched = [loc for loc in self.case_data.locations if loc.id not in state.explored_location_ids]
        if unsearched:
            return f"Lead: You haven't thoroughly searched the {unsearched[0].name} yet. Clues may be concealed there."

        # 2. Critical evidence unexamined
        critical_unfound = [
            e for e in self.case_data.evidence
            if e.is_critical and e.id not in state.discovered_evidence_ids
        ]
        if critical_unfound:
            return f"Forensics: A critical piece of physical evidence ({critical_unfound[0].name}) remains undiscovered in {critical_unfound[0].location_id}."

        # 3. Key suspect not interrogated
        interrogated = {t.suspect_id for t in state.interrogation_turns}
        unquestioned = [s for s in self.case_data.suspects if s.id not in interrogated]
        if unquestioned:
            return f"Interrogation: You have yet to question {unquestioned[0].name} ({unquestioned[0].role})."

        # 4. Confronting Dr. Croft
        croft_turns = [t for t in state.interrogation_turns if t.suspect_id == "dr_croft"]
        has_bag = "medical_bag" in state.discovered_evidence_ids
        has_audit = "audit_dossier" in state.discovered_evidence_ids

        if has_bag and has_audit and not any("medical_bag" in t.presented_evidence_ids for t in croft_turns):
            return "Breakthrough: You possess Dr. Croft's medical bag and Arthur's audit dossier. Present them directly to Dr. Croft in the Interrogation Room to break his alibi!"

        if state.detected_contradictions:
            return f"Evidence Ready: You have uncovered {len(state.detected_contradictions)} critical contradictions. Review the timeline and proceed to Accusation when ready."

        return "Review suspect alibis against the 10:14 PM time of death to isolate inconsistencies."
