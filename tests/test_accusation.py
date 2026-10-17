"""Unit tests for accusation evaluation, scoring, and verdict tiers."""

import pytest
from murderbox.engine.game_engine import GameEngine
from murderbox.models.investigation import AccusationSubmission


def test_perfect_accusation_solve():
    engine = GameEngine()
    # Discover all locations
    for loc in engine.case_data.locations:
        engine.search_location(loc.id)

    submission = AccusationSubmission(
        accused_suspect_id="dr_croft",
        selected_motive="Clinical trial fraud exposure, forged signatures, and imminent criminal indictment",
        selected_evidence_ids=["audit_dossier", "medical_bag", "scotch_decanter", "toxicology_report", "muddy_footprints"],
        closing_rationale="Dr. Croft faced ruined career and imprisonment from Arthur's audit, so he laced the decanter stopper with Compound V-7 at 9:45 PM.",
    )

    result = engine.submit_accusation(submission)

    assert result.is_culprit_correct is True
    assert result.culprit_score == 40
    assert result.motive_score >= 20
    assert result.evidence_score >= 20
    assert result.total_score >= 80
    assert result.rank_title in ("Master Detective", "Competent Sleuth")
    assert "Arthur was a tyrant" in result.culprit_confession


def test_wrongful_arrest():
    engine = GameEngine()
    submission = AccusationSubmission(
        accused_suspect_id="vincent_reed",
        selected_motive="Stolen patents and revenge",
        selected_evidence_ids=["compound_v7_vial"],
        closing_rationale="He grew the plants in the greenhouse.",
    )

    result = engine.submit_accusation(submission)

    assert result.is_culprit_correct is False
    assert result.culprit_score == 0
    assert result.total_score < 40
    assert result.rank_title == "Wrongful Arrest"
