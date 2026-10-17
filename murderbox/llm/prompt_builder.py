"""System prompt builder enforcing strict narrative boundaries and character personas."""

from typing import List, Optional
from murderbox.models.case import SuspectProfile, EvidenceItem


class SuspectPromptBuilder:
    """Constructs tailored system prompts for AI suspects with strict knowledge partitioning."""

    @staticmethod
    def build_system_prompt(
        suspect: SuspectProfile,
        presented_evidence: Optional[List[EvidenceItem]] = None,
        dialogue_history: Optional[str] = None,
    ) -> str:
        """Generates the authoritative system prompt for the suspect."""
        evidence_list = presented_evidence or []

        prompt_parts = [
            f"You are roleplaying as {suspect.name}, a {suspect.age}-year-old {suspect.role} in a classic noir murder mystery.",
            f"Personality: {suspect.personality}",
            f"Background: {suspect.public_bio}",
            f"Relationship to victim Arthur Vance: {suspect.relationship_to_victim}",
            "",
            "=== YOUR AUTHORIZED ALIBI & KNOWLEDGE ===",
            f"Claimed Alibi: {suspect.knowledge_boundaries.alibi_statement}",
            f"Allowed Topics you can discuss: {', '.join(suspect.knowledge_boundaries.allowed_topics)}",
            "",
            "=== STRICT KNOWLEDGE BOUNDARIES (NEVER VIOLATE) ===",
            "1. You only know what your character experienced firsthand. Do NOT invent facts about other rooms.",
            "2. Do NOT mention or leak these forbidden subjects:",
        ]

        for fb in suspect.knowledge_boundaries.forbidden_topics:
            prompt_parts.append(f"   - {fb}")

        if not suspect.is_culprit:
            prompt_parts.extend([
                "3. YOU ARE INNOCENT of the murder. You did not poison Arthur Vance.",
                "4. You do not know for certain who the killer is. Do not directly name anyone as the killer unless you personally witnessed them.",
                f"Your private secret (unrelated to the murder): {suspect.knowledge_boundaries.hidden_secret}",
            ])
        else:
            prompt_parts.extend([
                "3. YOU ARE THE CULPRIT. You poisoned Arthur Vance's scotch decanter with Compound V-7 at 9:45 PM.",
                "4. DECEPTION STRATEGY:",
                f"   {suspect.deception_strategy or 'Deny entering the study after 9:15 PM. Feign shock and clinical detachment.'}",
                "5. Only crack and confess if the detective confronts you simultaneously with your medical kit, the punctured decanter, and the audit dossier.",
            ])

        # Presented evidence section
        if evidence_list:
            prompt_parts.extend([
                "",
                "=== EVIDENCE PRESENTED BY THE DETECTIVE IN THIS TURN ===",
                "The detective is holding the following evidence in front of you:",
            ])
            for ev in evidence_list:
                prompt_parts.append(
                    f"- {ev.name} ({ev.category}): {ev.detailed_inspection}"
                )
            prompt_parts.append(
                "You MUST react directly and realistically to this evidence. If it is incriminating, show tension, defensiveness, or attempt to explain it away."
            )

        # Dialogue history section
        if dialogue_history:
            prompt_parts.extend([
                "",
                "=== YOUR PREVIOUS CONVERSATION WITH THE DETECTIVE ===",
                dialogue_history,
                "",
                "Maintain complete consistency with what you previously told the detective. Do not contradict yourself unless caught in a lie.",
            ])

        prompt_parts.extend([
            "",
            "=== ROLEPLAY INSTRUCTIONS ===",
            "- Stay in character at all times. Deliver natural, dramatic noir dialogue (2-4 sentences).",
            "- Never speak as an AI assistant. Never break character.",
            "- Express your authentic character voice and emotion.",
        ])

        return "\n".join(prompt_parts)
