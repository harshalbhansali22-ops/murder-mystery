"""Main deterministic game engine state machine for MurderBox."""

import uuid
from typing import List, Dict, Optional, Any
from murderbox.models.case import CaseData, EvidenceItem, Location, SuspectProfile
from murderbox.models.dialogue import InterrogationTurn, StatementClaim, ContradictionResult
from murderbox.models.investigation import InvestigationState, AccusationSubmission, AccusationResult
from murderbox.engine.case_loader import CaseLoader
from murderbox.engine.memory_manager import MemoryManager
from murderbox.engine.contradiction_analyzer import ContradictionAnalyzer
from murderbox.engine.validator import GroundTruthValidator


class GameEngine:
    """State machine governing locations, evidence discovery, turns, scoring, and case resolution."""

    def __init__(self, case_loader: Optional[CaseLoader] = None, memory_manager: Optional[MemoryManager] = None):
        self.loader = case_loader or CaseLoader()
        self.case_data: CaseData = self.loader.get_case()
        self.memory = memory_manager or MemoryManager(":memory:")
        self.contradiction_analyzer = ContradictionAnalyzer(self.case_data)
        self.validator = GroundTruthValidator(self.case_data)
        self.state = InvestigationState(case_id=self.case_data.case_id)

    def search_location(self, location_id: str) -> List[EvidenceItem]:
        """Explores a location in the manor, discovering any concealed clues."""
        loc = self.case_data.get_location(location_id)
        if not loc:
            raise ValueError(f"Unknown location ID: '{location_id}'")

        if location_id not in self.state.explored_location_ids:
            self.state.explored_location_ids.append(location_id)
            loc.searched = True

        newly_found: List[EvidenceItem] = []
        for ev_id in loc.evidence_ids:
            ev = self.case_data.get_evidence(ev_id)
            if ev:
                ev.discovered = True
                if ev_id not in self.state.discovered_evidence_ids:
                    self.state.discovered_evidence_ids.append(ev_id)
                    newly_found.append(ev)

        return newly_found

    def get_discovered_evidence(self) -> List[EvidenceItem]:
        """Returns all evidence items discovered so far."""
        return [
            self.case_data.get_evidence(ev_id)
            for ev_id in self.state.discovered_evidence_ids
            if self.case_data.get_evidence(ev_id) is not None
        ]

    def record_turn(self, turn: InterrogationTurn) -> None:
        """Stores a completed turn in state and persistent SQLite memory."""
        self.state.current_turn += 1
        self.state.interrogation_turns.append(turn)
        for c in turn.contradictions_found:
            self.state.detected_contradictions.append(c)
        self.memory.save_turn(turn)

    def add_notebook_note(self, note: str) -> None:
        """Adds a detective's observation note."""
        self.state.notebook_notes.append(note.strip())

    def submit_accusation(self, submission: AccusationSubmission) -> AccusationResult:
        """Evaluates the player's final accusation package against the ground-truth solution."""
        solution = self.case_data.solution
        is_culprit_correct = submission.accused_suspect_id == solution.culprit_id

        # 1. Culprit Score (40 pts)
        culprit_score = 40 if is_culprit_correct else 0

        # 2. Motive Score (25 pts)
        motive_keywords = ["audit", "fraud", "forged", "license", "clinical", "indictment", "trials", "ruin"]
        motive_text = submission.selected_motive.lower()
        matched_motive_kws = [kw for kw in motive_keywords if kw in motive_text]
        if is_culprit_correct and matched_motive_kws:
            motive_score = min(25, int(25 * (len(matched_motive_kws) / 3)))
        elif is_culprit_correct:
            motive_score = 10
        else:
            motive_score = 0

        # 3. Evidence Score (25 pts)
        key_evidence_set = set(solution.key_evidence_ids)
        submitted_evidence_set = set(submission.selected_evidence_ids)
        matched_evidence = key_evidence_set.intersection(submitted_evidence_set)
        evidence_score = int(25 * (len(matched_evidence) / len(key_evidence_set))) if key_evidence_set else 0

        # 4. Contradiction Bonus (10 pts)
        contradiction_bonus = min(10, len(self.state.detected_contradictions) * 2)

        total_score = culprit_score + motive_score + evidence_score + contradiction_bonus

        # Determine rank
        if total_score >= 90:
            rank = "Master Detective"
            verdict = (
                "Flawless deduction. You systematically dismantled the killer's alibi, "
                "caught every crucial contradiction, and assembled an airtight case that guarantees conviction."
            )
        elif total_score >= 70:
            rank = "Competent Sleuth"
            verdict = (
                "Solid police work. You accurately identified the killer and their motive, "
                "though a few forensic links remained unexamined."
            )
        elif total_score >= 40:
            rank = "Flawed Deduction"
            verdict = (
                "Incomplete investigation. While you connected some suspicious dots, the crown prosecutor "
                "faces an uphill battle due to missing critical physical evidence."
            )
        else:
            rank = "Wrongful Arrest"
            verdict = (
                "A catastrophic miscarriage of justice. An innocent person sits in handcuffs "
                "while the true mastermind slips into the shadows."
            )

        confession = solution.confession_text if is_culprit_correct else "The accused vehemently proclaims their innocence."

        result = AccusationResult(
            is_culprit_correct=is_culprit_correct,
            culprit_score=culprit_score,
            motive_score=motive_score,
            evidence_score=evidence_score,
            contradiction_bonus=contradiction_bonus,
            total_score=total_score,
            rank_title=rank,
            score_percentage=float(total_score),
            breakdown={
                "culprit_match": is_culprit_correct,
                "matched_evidence_count": len(matched_evidence),
                "total_key_evidence": len(key_evidence_set),
                "contradictions_caught": len(self.state.detected_contradictions),
            },
            narrative_verdict=verdict,
            culprit_confession=confession,
        )

        self.state.is_solved = is_culprit_correct
        self.state.final_result = result
        return result

    def reset_game(self) -> None:
        """Resets the game state and memory store."""
        self.state = InvestigationState(case_id=self.case_data.case_id)
        self.memory.clear()
        for loc in self.case_data.locations:
            loc.searched = False
        for ev in self.case_data.evidence:
            ev.discovered = False
