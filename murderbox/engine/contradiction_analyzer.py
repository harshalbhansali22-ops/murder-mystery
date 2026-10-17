"""Contradiction detection engine for suspect testimonies."""

import re
import uuid
from typing import List, Dict, Optional, Any, Set
from murderbox.models.dialogue import (
    StatementClaim,
    ContradictionResult,
    ContradictionType,
    ContradictionSeverity,
)
from murderbox.models.case import CaseData, EvidenceItem, SuspectProfile


class ContradictionAnalyzer:
    """Analyzes suspect statements for self-contradictions, evidence conflicts, and inter-suspect conflicts."""

    def __init__(self, case_data: CaseData):
        self.case_data = case_data

    def extract_claims(self, suspect_id: str, turn_id: str, text: str) -> List[StatementClaim]:
        """Extracts atomic factual claims from suspect utterances using pattern matching."""
        claims: List[StatementClaim] = []
        lower = text.lower()

        # Check for time markers
        time_matches = re.findall(r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm|o'clock)?)\b", lower)
        # Check for location markers
        locations_known = [
            ("guest suite", "guest_suite"),
            ("guest room", "guest_suite"),
            ("my room", "guest_suite"),
            ("drawing room", "drawing_room"),
            ("study", "study"),
            ("library", "library"),
            ("conservatory", "conservatory"),
            ("greenhouse", "conservatory"),
            ("kitchen", "kitchen_pantry"),
            ("pantry", "kitchen_pantry"),
            ("terrace", "terrace"),
            ("rose garden", "garden"),
            ("garden", "garden"),
        ]

        # Scan for denials
        denial_patterns = [
            r"never (?:left|stepped|went|entered|visited) (?:the )?([a-z\s]+)",
            r"never touched (?:the )?([a-z\s]+)",
            r"was (?:in|at) (?:the )?([a-z\s]+) (?:all night|the entire evening|all evening)",
            r"stayed in (?:my|the) ([a-z\s]+)",
        ]

        for pattern in denial_patterns:
            matches = re.findall(pattern, lower)
            for m in matches:
                claims.append(
                    StatementClaim(
                        claim_id=f"claim_{uuid.uuid4().hex[:8]}",
                        suspect_id=suspect_id,
                        turn_id=turn_id,
                        text=f"Denial: {m.strip()}",
                        entity=m.strip(),
                        claim_type="denial",
                    )
                )

        # Identify claimed locations
        for loc_str, loc_key in locations_known:
            if loc_str in lower:
                matched_time = time_matches[0] if time_matches else None
                claims.append(
                    StatementClaim(
                        claim_id=f"claim_{uuid.uuid4().hex[:8]}",
                        suspect_id=suspect_id,
                        turn_id=turn_id,
                        text=f"Claimed presence at {loc_str}",
                        claimed_location=loc_key,
                        claimed_time=matched_time,
                        claim_type="alibi",
                    )
                )
                break

        # Fallback claim if none matched
        if not claims and len(text.strip()) > 10:
            claims.append(
                StatementClaim(
                    claim_id=f"claim_{uuid.uuid4().hex[:8]}",
                    suspect_id=suspect_id,
                    turn_id=turn_id,
                    text=text[:120].strip(),
                    claim_type="statement",
                )
            )

        return claims

    def analyze_turn(
        self,
        suspect_id: str,
        response_text: str,
        past_claims: List[StatementClaim],
        discovered_evidence: List[EvidenceItem],
        presented_evidence: List[EvidenceItem],
        all_suspect_claims: Optional[List[StatementClaim]] = None,
    ) -> List[ContradictionResult]:
        """Runs the four contradiction vectors across the response."""
        contradictions: List[ContradictionResult] = []
        lower_response = response_text.lower()

        # 1. Evidence Contradictions (direct conflict with presented or discovered clues)
        eval_evidence = list({e.id: e for e in (discovered_evidence + presented_evidence)}.values())
        for ev in eval_evidence:
            for kw in ev.contradiction_keywords:
                if kw.lower() in lower_response:
                    contradictions.append(
                        ContradictionResult(
                            type=ContradictionType.EVIDENCE_CONTRADICTION,
                            severity=ContradictionSeverity.HIGH,
                            description=(
                                f"Statement conflicts with {ev.name}: suspect claimed '{kw}', "
                                f"but forensic inspection of {ev.name} proves: {ev.detailed_inspection[:100]}..."
                            ),
                            suspect_id=suspect_id,
                            claim_text=kw,
                            conflicting_source=ev.name,
                            conflicting_detail=ev.detailed_inspection,
                        )
                    )
                    break

        # Specific evidence rules for Dr. Croft
        if suspect_id == "dr_croft":
            # If Croft claims he never left his room or never went outside
            claims_room_only = any(
                p in lower_response
                for p in ["never left my room", "never set foot in", "stayed in my guest suite", "never went outside"]
            )
            # Check footprints
            has_footprints = any(e.id == "muddy_footprints" for e in eval_evidence)
            if claims_room_only and has_footprints:
                contradictions.append(
                    ContradictionResult(
                        type=ContradictionType.EVIDENCE_CONTRADICTION,
                        severity=ContradictionSeverity.HIGH,
                        description=(
                            "Dr. Croft claims he never left his suite, directly contradicting the muddy bespoke "
                            "orthopedic brogue footprints tracked onto the study patio."
                        ),
                        suspect_id=suspect_id,
                        claim_text="Never left room",
                        conflicting_source="Bespoke Leather Shoe Prints",
                        conflicting_detail="Footprints match Dr. Croft's unique footwear.",
                    )
                )

            # Check medical bag
            claims_clean_bag = any(
                p in lower_response
                for p in ["untouched", "only brought vitamins", "never had sedatives", "satchel was never opened"]
            )
            has_bag = any(e.id == "medical_bag" for e in eval_evidence)
            if claims_clean_bag and has_bag:
                contradictions.append(
                    ContradictionResult(
                        type=ContradictionType.EVIDENCE_CONTRADICTION,
                        severity=ContradictionSeverity.HIGH,
                        description=(
                            "Dr. Croft claims his kit contained no sedatives, but inspection of his medical bag "
                            "reveals a missing Compound V-7 ampoule and discarded needle sheath."
                        ),
                        suspect_id=suspect_id,
                        claim_text="Kit untouched / no sedatives",
                        conflicting_source="Dr. Croft's Professional Medical Kit",
                        conflicting_detail="Empty sedative slot and used syringe sheath found in his satchel.",
                    )
                )

        # 2. Self-Contradictions (conflict with previous claims by this suspect)
        past_locations = {c.claimed_location for c in past_claims if c.claimed_location}
        current_claims = self.extract_claims(suspect_id, "temp", response_text)
        for cc in current_claims:
            if cc.claimed_location and past_locations and cc.claimed_location not in past_locations:
                # Suspect claims a different location than previously stated
                contradictions.append(
                    ContradictionResult(
                        type=ContradictionType.SELF_CONTRADICTION,
                        severity=ContradictionSeverity.MEDIUM,
                        description=(
                            f"Alibi shift: previously claimed to be at {', '.join(past_locations)}, "
                            f"now claims presence at {cc.claimed_location}."
                        ),
                        suspect_id=suspect_id,
                        claim_text=cc.text,
                        conflicting_source="Previous Testimony",
                        conflicting_detail=f"Earlier alibi placed suspect in {list(past_locations)[0]}.",
                    )
                )

        # 3. Inter-Suspect Conflicts (conflict with statements of other key witnesses)
        if suspect_id == "dr_croft":
            # Clara's established fact: saw Croft outside study at 9:30 PM
            claims_in_room_at_930 = any(
                p in lower_response
                for p in ["in my room at 9:30", "retired at 9:15", "in my suite from 9:15"]
            )
            if claims_in_room_at_930:
                has_kitchen_slip = any(e.id == "kitchen_order_slip" for e in eval_evidence)
                if has_kitchen_slip:
                    contradictions.append(
                        ContradictionResult(
                            type=ContradictionType.INTER_SUSPECT_CONFLICT,
                            severity=ContradictionSeverity.HIGH,
                            description=(
                                "Dr. Croft claims he was in his room by 9:15 PM, but Clara Dupont's verified "
                                "testimony and service slip state he was lingering directly outside Arthur's study door at 9:30 PM."
                            ),
                            suspect_id=suspect_id,
                            claim_text="In room from 9:15 PM onward",
                            conflicting_source="Clara Dupont / Evening Service Slip",
                            conflicting_detail="Observed outside study at 9:30 PM.",
                        )
                    )

        # 4. Ground-Truth Conflicts
        ground_truth_errors = [
            ("gunshot", "Cause of death is cardiovascular collapse via Compound V-7, not a gunshot wound."),
            ("stab wound", "Cause of death is toxicological cardiac arrest, not a stab wound."),
            ("died at midnight", "Arthur Vance died at 10:14 PM according to forensic pocket watch jamming."),
        ]
        for term, explanation in ground_truth_errors:
            if term in lower_response:
                contradictions.append(
                    ContradictionResult(
                        type=ContradictionType.GROUND_TRUTH_CONFLICT,
                        severity=ContradictionSeverity.HIGH,
                        description=f"Suspect made a false statement about the crime scene facts: {explanation}",
                        suspect_id=suspect_id,
                        claim_text=term,
                        conflicting_source="Forensic Ground Truth",
                        conflicting_detail=explanation,
                    )
                )

        return contradictions
