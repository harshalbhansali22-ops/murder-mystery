"""Reusable Streamlit UI widgets and components for MurderBox."""

import streamlit as st
from typing import List, Dict, Any, Optional
from murderbox.models.case import SuspectProfile, EvidenceItem
from murderbox.models.dialogue import InterrogationTurn, ContradictionResult
from murderbox.models.investigation import AccusationResult


def render_header(title: str, subtitle: str) -> None:
    """Renders the atmospheric title and subtitle."""
    st.markdown(f'<div class="noir-title">🕵️ {title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="noir-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def render_investigation_meter(metrics: Dict[str, Any]) -> None:
    """Displays top investigation status bar."""
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Clues Uncovered", value=metrics.get("evidence_discovered", "0/0"))
    with col2:
        st.metric(label="Suspects Questioned", value=metrics.get("suspects_questioned", "0/0"))
    with col3:
        st.metric(label="Contradictions Caught", value=str(metrics.get("contradictions_caught", 0)))
    with col4:
        readiness = metrics.get("investigation_readiness", 0)
        st.metric(label="Case Readiness", value=f"{readiness}%")
    st.progress(readiness / 100.0)


def render_suspect_card(suspect: SuspectProfile, times_questioned: int = 0) -> None:
    """Renders a character dossier card."""
    card_class = "noir-card noir-card-gold" if times_questioned > 0 else "noir-card"
    status_tag = f"⭐ Questioned ({times_questioned} turns)" if times_questioned > 0 else "⚪ Not Questioned"

    st.markdown(
        f"""
        <div class="{card_class}">
            <div style="display: flex; justify-content: space-between; align-items: baseline;">
                <h3 style="margin: 0; color: #f0f6fc;">{suspect.avatar_emoji} {suspect.name} ({suspect.age})</h3>
                <span style="font-size: 0.85rem; color: #8b949e;">{status_tag}</span>
            </div>
            <p style="color: #d4af37; font-weight: bold; margin: 4px 0;">{suspect.role}</p>
            <p style="color: #c9d1d9; font-size: 0.95rem;">{suspect.personality}</p>
            <div style="background: #0d1117; padding: 10px; border-radius: 6px; font-size: 0.9rem; margin-top: 8px;">
                <span style="color: #8b949e; font-weight: bold;">Claimed Alibi:</span> {suspect.alibi}<br/>
                <span style="color: #8b949e; font-weight: bold;">Relationship:</span> {suspect.relationship_to_victim}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_evidence_card(evidence: EvidenceItem) -> None:
    """Renders an evidence locker card with forensic analysis."""
    badge_style = "evidence-badge" if evidence.is_critical else "evidence-badge"
    critical_text = "🚨 CRITICAL CLUE" if evidence.is_critical else "CLUE"

    with st.container():
        st.markdown(
            f"""
            <div class="noir-card noir-card-critical">
                <span class="{badge_style}">{critical_text} • {evidence.category}</span>
                <h3 style="margin-top: 4px; color: #f0f6fc;">🔍 {evidence.name}</h3>
                <p style="color: #c9d1d9; font-size: 0.95rem;">{evidence.description}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander(f"🔬 Forensic Crime Lab Report: {evidence.name}", expanded=False):
            st.markdown(f"**Laboratory Analysis:**\n\n{evidence.detailed_inspection}")
            if evidence.contradiction_keywords:
                st.caption(f"Contradiction triggers: {', '.join(evidence.contradiction_keywords)}")


def render_contradiction_banner(contradiction: ContradictionResult) -> None:
    """Renders a prominent alert for caught lies and contradictions."""
    st.markdown(
        f"""
        <div class="contradiction-badge">
            <strong>⚠️ CONTRADICTION DETECTED [{contradiction.type.value.upper()}]</strong><br/>
            <span>{contradiction.description}</span><br/>
            <small style="color: #ffcccc;">Source: {contradiction.conflicting_source} | Claim: "{contradiction.claim_text}"</small>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dialogue_turn(turn: InterrogationTurn, suspect_name: str) -> None:
    """Renders an interrogation exchange with speech bubbles."""
    st.markdown(
        f"""
        <div class="chat-bubble-detective">
            <strong>🕵️ Detective:</strong> {turn.question}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if turn.presented_evidence_ids:
        clues_str = ", ".join(turn.presented_evidence_ids)
        st.caption(f"📁 Presented Evidence: {clues_str}")

    st.markdown(
        f"""
        <div class="chat-bubble-suspect">
            <strong>🗣️ {suspect_name}:</strong> {turn.response}
        </div>
        """,
        unsafe_allow_html=True,
    )

    for c in turn.contradictions_found:
        render_contradiction_banner(c)


def render_verdict_card(result: AccusationResult) -> None:
    """Displays the final accusation score and resolution."""
    status_color = "#38bdf8" if result.is_culprit_correct else "#ef4444"
    st.markdown(
        f"""
        <div class="noir-card" style="border: 2px solid {status_color}; text-align: center; padding: 24px;">
            <h1 style="color: {status_color}; margin: 0; font-size: 2.5rem;">{result.rank_title}</h1>
            <h2 style="color: #d4af37; margin: 8px 0;">Total Score: {result.total_score} / 100</h2>
            <p style="color: #c9d1d9; font-size: 1.1rem; max-width: 700px; margin: 12px auto;">
                {result.narrative_verdict}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Culprit Identification", f"{result.culprit_score} / 40")
    with col2:
        st.metric("Motive Deduction", f"{result.motive_score} / 25")
    with col3:
        st.metric("Evidence Quality", f"{result.evidence_score} / 25")
    with col4:
        st.metric("Contradiction Bonus", f"{result.contradiction_bonus} / 10")

    if result.culprit_confession:
        st.markdown("### 🎙️ Culprit's Confession")
        st.info(f'"{result.culprit_confession}"')
