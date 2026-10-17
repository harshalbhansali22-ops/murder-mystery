"""Unit tests for ContradictionAnalyzer."""

import pytest
from murderbox.engine.case_loader import CaseLoader
from murderbox.engine.contradiction_analyzer import ContradictionAnalyzer
from murderbox.models.dialogue import StatementClaim, ContradictionType


@pytest.fixture
def analyzer():
    loader = CaseLoader()
    return ContradictionAnalyzer(loader.get_case())


def test_evidence_contradiction_footprints(analyzer):
    footprints = analyzer.case_data.get_evidence("muddy_footprints")
    assert footprints is not None

    response = "I stayed in my guest suite the entire evening and never went outside."
    contradictions = analyzer.analyze_turn(
        suspect_id="dr_croft",
        response_text=response,
        past_claims=[],
        discovered_evidence=[footprints],
        presented_evidence=[footprints],
    )

    assert len(contradictions) > 0
    assert any(c.type == ContradictionType.EVIDENCE_CONTRADICTION for c in contradictions)


def test_evidence_contradiction_medical_bag(analyzer):
    bag = analyzer.case_data.get_evidence("medical_bag")
    assert bag is not None

    response = "My medical satchel was untouched; I never had sedatives with me tonight."
    contradictions = analyzer.analyze_turn(
        suspect_id="dr_croft",
        response_text=response,
        past_claims=[],
        discovered_evidence=[bag],
        presented_evidence=[bag],
    )

    assert len(contradictions) > 0
    types = [c.type for c in contradictions]
    assert ContradictionType.EVIDENCE_CONTRADICTION in types


def test_self_contradiction_alibi_shift(analyzer):
    past_claim = StatementClaim(
        claim_id="p1",
        suspect_id="elena_vance",
        turn_id="t0",
        text="I was in the drawing room reading.",
        claimed_location="drawing_room",
        claim_type="alibi",
    )

    # New response claims presence at conservatory
    new_response = "I was actually in the conservatory checking the orchids."
    contradictions = analyzer.analyze_turn(
        suspect_id="elena_vance",
        response_text=new_response,
        past_claims=[past_claim],
        discovered_evidence=[],
        presented_evidence=[],
    )

    assert len(contradictions) > 0
    assert any(c.type == ContradictionType.SELF_CONTRADICTION for c in contradictions)


def test_ground_truth_conflict_gunshot(analyzer):
    response = "Arthur was struck down by a gunshot wound in his chair."
    contradictions = analyzer.analyze_turn(
        suspect_id="marcus_sterling",
        response_text=response,
        past_claims=[],
        discovered_evidence=[],
        presented_evidence=[],
    )

    assert len(contradictions) > 0
    assert any(c.type == ContradictionType.GROUND_TRUTH_CONFLICT for c in contradictions)
