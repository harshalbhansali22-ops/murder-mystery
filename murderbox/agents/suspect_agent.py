"""SuspectAgent coordinating LLM generation, memory retrieval, validation, and contradiction detection."""

import uuid
import time
from typing import List, Optional, Dict, Any
from murderbox.models.case import SuspectProfile, EvidenceItem, CaseData
from murderbox.models.dialogue import InterrogationTurn, StatementClaim, ContradictionResult
from murderbox.engine.memory_manager import MemoryManager
from murderbox.engine.contradiction_analyzer import ContradictionAnalyzer
from murderbox.engine.validator import GroundTruthValidator
from murderbox.llm.sarvam_client import SarvamClient


class SuspectAgent:
    """Autonomous agent orchestrating a specific suspect's behavior and interrogation responses."""

    def __init__(
        self,
        suspect: SuspectProfile,
        case_data: CaseData,
        memory_manager: MemoryManager,
        contradiction_analyzer: ContradictionAnalyzer,
        validator: GroundTruthValidator,
        sarvam_client: Optional[SarvamClient] = None,
    ):
        self.suspect = suspect
        self.case_data = case_data
        self.memory = memory_manager
        self.analyzer = contradiction_analyzer
        self.validator = validator
        self.client = sarvam_client or SarvamClient()

    def interrogate(
        self,
        question: str,
        presented_evidence: Optional[List[EvidenceItem]] = None,
        discovered_evidence: Optional[List[EvidenceItem]] = None,
    ) -> InterrogationTurn:
        """Executes a full interrogation cycle for this suspect."""
        presented = presented_evidence or []
        discovered = discovered_evidence or []
        turn_id = f"turn_{uuid.uuid4().hex[:8]}"

        # 1. Retrieve dialogue history from persistent memory
        history_str = self.memory.get_formatted_dialogue_context(self.suspect.id, limit=6)

        # 2. Query LLM / Mock provider
        generation_result = self.client.generate_suspect_response(
            suspect=self.suspect,
            user_query=question,
            presented_evidence=presented,
            dialogue_history=history_str,
        )
        raw_text = generation_result["text"]
        model_name = generation_result.get("model", "mock")
        is_fallback = generation_result.get("is_fallback", False)

        # 3. Pass through Ground-Truth Validator to enforce knowledge boundaries
        presented_ids = [e.id for e in presented]
        validated_text, was_modified, mod_reason = self.validator.validate_and_guard(
            suspect=self.suspect,
            raw_text=raw_text,
            presented_evidence_ids=presented_ids,
        )

        # 4. Extract atomic claims from the validated response
        claims = self.analyzer.extract_claims(self.suspect.id, turn_id, validated_text)

        # 5. Run Contradiction Analyzer
        past_claims = self.memory.get_claims_by_suspect(self.suspect.id)
        all_claims = self.memory.get_all_claims()
        contradictions = self.analyzer.analyze_turn(
            suspect_id=self.suspect.id,
            response_text=validated_text,
            past_claims=past_claims,
            discovered_evidence=discovered,
            presented_evidence=presented,
            all_suspect_claims=all_claims,
        )

        # Mark claims that triggered contradictions
        if contradictions:
            for c in claims:
                for cr in contradictions:
                    if cr.claim_text.lower() in c.text.lower():
                        c.is_contradiction = True

        # 6. Build the InterrogationTurn
        turn = InterrogationTurn(
            turn_id=turn_id,
            suspect_id=self.suspect.id,
            question=question,
            presented_evidence_ids=presented_ids,
            response=validated_text,
            claims=claims,
            contradictions_found=contradictions,
            model_name=model_name,
            is_fallback=is_fallback,
            timestamp=time.time(),
        )

        # 7. Persist turn and claims in SQLite memory
        self.memory.save_turn(turn)

        return turn
