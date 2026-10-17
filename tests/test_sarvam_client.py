"""Unit tests for SarvamClient, MockProvider, and PromptBuilder."""

import pytest
from murderbox.engine.case_loader import CaseLoader
from murderbox.llm.sarvam_client import SarvamClient
from murderbox.llm.mock_provider import MockProvider
from murderbox.llm.prompt_builder import SuspectPromptBuilder


@pytest.fixture
def case_data():
    return CaseLoader().get_case()


def test_mock_provider_croft_alibi(case_data):
    provider = MockProvider()
    croft = case_data.get_suspect("dr_croft")

    reply = provider.generate_response(croft, "Where were you at 9:30 PM?", [])
    assert "guest suite" in reply.lower() or "9:15" in reply.lower()


def test_mock_provider_croft_confession_on_dual_evidence(case_data):
    provider = MockProvider()
    croft = case_data.get_suspect("dr_croft")
    bag = case_data.get_evidence("medical_bag")
    audit = case_data.get_evidence("audit_dossier")

    reply = provider.generate_response(croft, "Confess!", presented_evidence=[bag, audit])
    assert "tyrant" in reply.lower() or "audit dossier" in reply.lower()


def test_sarvam_client_fallback_mode(case_data):
    client = SarvamClient(force_mock=True)
    elena = case_data.get_suspect("elena_vance")

    res = client.generate_suspect_response(elena, "Where were you?")
    assert "text" in res
    assert res["is_fallback"] is True
    assert len(res["text"]) > 10


def test_prompt_builder_structure(case_data):
    croft = case_data.get_suspect("dr_croft")
    prompt = SuspectPromptBuilder.build_system_prompt(croft)

    assert "Dr. Julian Croft" in prompt
    assert "Personal Physician" in prompt
    assert "CULPRIT" in prompt
    assert "STRICT KNOWLEDGE BOUNDARIES" in prompt
