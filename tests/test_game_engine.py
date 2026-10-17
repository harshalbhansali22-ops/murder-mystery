"""Unit tests for GameEngine state machine and gameplay loop."""

import pytest
from murderbox.engine.case_loader import CaseLoader
from murderbox.engine.game_engine import GameEngine
from murderbox.engine.memory_manager import MemoryManager
from murderbox.models.dialogue import InterrogationTurn


def test_search_location():
    loader = CaseLoader()
    engine = GameEngine(case_loader=loader)

    # Search study
    clues = engine.search_location("study")
    assert len(clues) > 0
    assert "study" in engine.state.explored_location_ids

    discovered_ids = [e.id for e in engine.get_discovered_evidence()]
    for c in clues:
        assert c.id in discovered_ids


def test_record_turn():
    engine = GameEngine()
    initial_turns = engine.state.current_turn

    turn = InterrogationTurn(
        turn_id="t_test",
        suspect_id="elena_vance",
        question="What book were you reading?",
        response="A collection of Chopin nocturnes and poetry.",
    )

    engine.record_turn(turn)
    assert engine.state.current_turn == initial_turns + 1
    assert len(engine.state.interrogation_turns) == 1

    # Verify saved in persistent memory
    memory_turns = engine.memory.get_suspect_turns("elena_vance")
    assert len(memory_turns) == 1
    assert memory_turns[0].question == "What book were you reading?"


def test_notebook_notes():
    engine = GameEngine()
    engine.add_notebook_note("Croft was seen by Evelyn near patio.")
    assert len(engine.state.notebook_notes) == 1
    assert "Croft" in engine.state.notebook_notes[0]
