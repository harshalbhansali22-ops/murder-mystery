"""Unit tests for CaseLoader and case data integrity."""

import pytest
from murderbox.engine.case_loader import CaseLoader
from murderbox.models.case import CaseData


def test_load_default_case():
    loader = CaseLoader()
    case = loader.get_case()

    assert case.case_id == "the_vance_mystery"
    assert case.victim_name == "Arthur Vance"
    assert len(case.suspects) == 6
    assert len(case.locations) == 6
    assert len(case.evidence) >= 10
    assert len(case.timeline) >= 6


def test_suspect_profiles():
    loader = CaseLoader()
    suspect_ids = {s.id for s in loader.get_case().suspects}

    expected_ids = {"elena_vance", "dr_croft", "marcus_sterling", "clara_dupont", "vincent_reed", "evelyn_cross"}
    assert suspect_ids == expected_ids

    culprit = loader.get_suspect("dr_croft")
    assert culprit is not None
    assert culprit.is_culprit is True
    assert culprit.role == "Personal Physician"


def test_evidence_integrity():
    loader = CaseLoader()
    case = loader.get_case()

    location_ids = {loc.id for loc in case.locations}
    for ev in case.evidence:
        assert ev.location_id in location_ids
        assert len(ev.name) > 0
        assert len(ev.detailed_inspection) > 0


def test_solution_integrity():
    loader = CaseLoader()
    case = loader.get_case()

    assert case.solution.culprit_id == "dr_croft"
    assert len(case.solution.key_evidence_ids) >= 3
    assert len(case.solution.confession_text) > 20
