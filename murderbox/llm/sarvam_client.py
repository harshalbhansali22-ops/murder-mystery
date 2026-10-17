"""Sarvam AI client supporting OpenAI-compatible chat completions with mock fallback."""

import os
import requests
import json
import logging
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv
from murderbox.models.case import SuspectProfile, EvidenceItem
from murderbox.llm.mock_provider import MockProvider
from murderbox.llm.prompt_builder import SuspectPromptBuilder

load_dotenv()

logger = logging.getLogger(__name__)


class SarvamClient:
    """Client for Sarvam AI chat completions with automatic fallback to high-fidelity mock."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 15,
        force_mock: Optional[bool] = None,
    ):
        self.api_key = api_key or os.getenv("SARVAM_API_KEY", "").strip()
        self.base_url = (base_url or os.getenv("SARVAM_BASE_URL", "https://api.sarvam.ai/v1")).rstrip("/")
        self.model = model or os.getenv("SARVAM_MODEL", "sarvam-105b")
        self.timeout = timeout

        env_force_mock = os.getenv("MURDERBOX_MOCK_LLM", "false").lower() in ("true", "1", "yes")
        self.use_mock = force_mock if force_mock is not None else (env_force_mock or not self.api_key)
        self.mock_provider = MockProvider()

    def generate_suspect_response(
        self,
        suspect: SuspectProfile,
        user_query: str,
        presented_evidence: Optional[List[EvidenceItem]] = None,
        dialogue_history: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generates a character response using Sarvam AI API or the deterministic mock.
        Returns a dict: {"text": str, "model": str, "is_fallback": bool}
        """
        if self.use_mock or not self.api_key:
            reply = self.mock_provider.generate_response(
                suspect=suspect,
                user_query=user_query,
                presented_evidence=presented_evidence,
                dialogue_history=dialogue_history,
            )
            return {"text": reply, "model": "mock-sarvam-provider", "is_fallback": True}

        system_prompt = SuspectPromptBuilder.build_system_prompt(
            suspect=suspect,
            presented_evidence=presented_evidence,
            dialogue_history=dialogue_history,
        )

        headers = {
            "Content-Type": "application/json",
            "api-subscription-key": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query},
            ],
            "temperature": 0.4,
            "max_tokens": 250,
        }

        endpoint = f"{self.base_url}/chat/completions"

        for attempt in range(2):
            try:
                response = requests.post(endpoint, json=payload, headers=headers, timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    choices = data.get("choices", [])
                    if choices and "message" in choices[0]:
                        content = choices[0]["message"].get("content", "").strip()
                        if content:
                            return {"text": content, "model": self.model, "is_fallback": False}
                else:
                    logger.warning(
                        "Sarvam API returned HTTP %d: %s (attempt %d/2)",
                        response.status_code,
                        response.text,
                        attempt + 1,
                    )
            except Exception as e:
                logger.warning("Error connecting to Sarvam API: %s (attempt %d/2)", str(e), attempt + 1)

        # Fallback to mock on error
        reply = self.mock_provider.generate_response(
            suspect=suspect,
            user_query=user_query,
            presented_evidence=presented_evidence,
            dialogue_history=dialogue_history,
        )
        return {"text": reply, "model": "mock-sarvam-fallback", "is_fallback": True}
