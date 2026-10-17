"""Ground-truth validator and information boundary guard for suspect outputs."""

import re
from typing import Tuple, List, Optional
from murderbox.models.case import CaseData, SuspectProfile


class GroundTruthValidator:
    """Enforces strict narrative consistency and prevents premature spoiler leaks or out-of-character hallucinations."""

    def __init__(self, case_data: CaseData):
        self.case_data = case_data

    def validate_and_guard(
        self,
        suspect: SuspectProfile,
        raw_text: str,
        presented_evidence_ids: Optional[List[str]] = None,
    ) -> Tuple[str, bool, Optional[str]]:
        """
        Validates the generated suspect utterance against boundaries.
        Returns:
            Tuple[sanitized_text, was_modified, reason]
        """
        presented_ids = presented_evidence_ids or []
        lower = raw_text.lower()

        # 1. Non-culprit confession guard
        if not suspect.is_culprit:
            confession_phrases = [
                "i killed arthur",
                "i murdered arthur",
                "i poisoned the decanter",
                "i poisoned arthur",
                "i slipped the compound",
                "it was me who killed him",
            ]
            for cp in confession_phrases:
                if cp in lower:
                    fallback = suspect.deflection_phrases[0] if suspect.deflection_phrases else (
                        "I had no part in Arthur's death, detective. Don't put words in my mouth."
                    )
                    return fallback, True, f"Prevented false confession from non-culprit '{suspect.id}'."

        # 2. Premature culprit naming guard (Non-witness naming Dr. Croft as the killer without seeing it)
        if not suspect.is_culprit and suspect.id != "evelyn_cross":
            premature_spoilers = [
                "dr. croft killed arthur",
                "croft is the murderer",
                "croft poisoned the decanter",
                "croft poisoned the scotch",
                "dr. croft did it",
            ]
            for ps in premature_spoilers:
                if ps in lower:
                    fallback = (
                        "Arthur had strained relationships with everyone, detective, especially his senior staff. "
                        "You should look at everyone's movements tonight."
                    )
                    return fallback, True, "Filtered premature direct accusation of culprit without evidentiary basis."

        # 3. Culprit confession guard: Dr. Croft should only confess if key evidence is presented
        if suspect.is_culprit:
            confession_signals = ["i confess", "i slipped the compound", "god help me", "i killed him"]
            has_confession = any(cs in lower for cs in confession_signals)
            
            # Check if key evidence was presented: audit_dossier, medical_bag, scotch_decanter
            required_for_confession = {"medical_bag", "audit_dossier"}
            has_required = required_for_confession.issubset(set(presented_ids))
            
            if has_confession and not has_required:
                deflection = (
                    "You're fabricating wild theories, detective. Arthur was an ailing patient under severe stress. "
                    "Unless you have definitive clinical evidence connecting me to his sudden cardiac event, "
                    "I suggest you mind your tone."
                )
                return deflection, True, "Suppressed premature culprit confession before critical evidence confrontation."

        # 4. Filter forbidden topics defined in the suspect profile
        for forbidden in suspect.knowledge_boundaries.forbidden_topics:
            if forbidden.lower() in lower and len(forbidden) > 5:
                # Sanitize out the specific forbidden leak
                cleaned = re.sub(re.escape(forbidden), "[redacted]", raw_text, flags=re.IGNORECASE)
                return cleaned, True, f"Redacted forbidden topic '{forbidden}'."

        return raw_text, False, None
