"""Unit tests for SQLite MemoryManager."""

import pytest
import time
from murderbox.engine.memory_manager import MemoryManager
from murderbox.models.dialogue import (
    InterrogationTurn,
    StatementClaim,
    ContradictionResult,
    ContradictionType,
    ContradictionSeverity,
)


def test_save_and_retrieve_turn():
    mem = MemoryManager(":memory:")

    claim = StatementClaim(
        claim_id="c1",
        suspect_id="dr_croft",
        turn_id="t1",
        text="I was in my room at 9:15 PM.",
        claimed_location="guest_suite",
        claimed_time="9:15 PM",
        claim_type="alibi",
    )

    contra = ContradictionResult(
        type=ContradictionType.EVIDENCE_CONTRADICTION,
        severity=ContradictionSeverity.HIGH,
        description="Footprints conflict with alibi.",
        suspect_id="dr_croft",
        claim_text="Never left room",
        conflicting_source="Bespoke Shoes",
        conflicting_detail="Footprints match.",
    )

    turn = InterrogationTurn(
        turn_id="t1",
        suspect_id="dr_croft",
        question="Where were you?",
        presented_evidence_ids=["muddy_footprints"],
        response="I stayed in my room.",
        claims=[claim],
        contradictions_found=[contra],
    )

    mem.save_turn(turn)

    retrieved = mem.get_suspect_turns("dr_croft")
    assert len(retrieved) == 1
    assert retrieved[0].turn_id == "t1"
    assert retrieved[0].question == "Where were you?"
    assert retrieved[0].presented_evidence_ids == ["muddy_footprints"]
    assert len(retrieved[0].contradictions_found) == 1
    assert retrieved[0].contradictions_found[0].type == ContradictionType.EVIDENCE_CONTRADICTION


def test_dialogue_context_formatting():
    mem = MemoryManager(":memory:")

    turn1 = InterrogationTurn(
        turn_id="t1",
        suspect_id="elena_vance",
        question="Where were you at 9:00 PM?",
        response="In the drawing room reading.",
    )
    turn2 = InterrogationTurn(
        turn_id="t2",
        suspect_id="elena_vance",
        question="Did you see anyone?",
        response="Only the rain lashing against the glass.",
    )

    mem.save_turn(turn1)
    mem.save_turn(turn2)

    context = mem.get_formatted_dialogue_context("elena_vance", limit=2)
    assert "In the drawing room reading." in context
    assert "Only the rain lashing against the glass." in context


def test_clear_memory():
    mem = MemoryManager(":memory:")
    turn = InterrogationTurn(
        turn_id="t1",
        suspect_id="vincent_reed",
        question="Are you the groundsman?",
        response="I tend the conservatory.",
    )
    mem.save_turn(turn)
    assert len(mem.get_all_turns()) == 1

    mem.clear()
    assert len(mem.get_all_turns()) == 0
