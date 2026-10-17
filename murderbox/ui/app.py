"""MurderBox: Interactive AI Murder Mystery Streamlit Application."""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List

from murderbox.engine.case_loader import CaseLoader
from murderbox.engine.game_engine import GameEngine
from murderbox.engine.memory_manager import MemoryManager
from murderbox.engine.contradiction_analyzer import ContradictionAnalyzer
from murderbox.engine.validator import GroundTruthValidator
from murderbox.llm.sarvam_client import SarvamClient
from murderbox.agents.suspect_agent import SuspectAgent
from murderbox.agents.game_master import GameMasterAgent
from murderbox.models.investigation import AccusationSubmission
from murderbox.evaluation.benchmark import AgentBenchmarkEngine
from murderbox.ui.styles import get_noir_css
import murderbox.ui.components as ui


# Page configuration
st.set_page_config(
    page_title="MurderBox — The Vance Manor Mystery",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom Noir CSS
st.markdown(get_noir_css(), unsafe_allow_html=True)


def init_session_state():
    """Initializes persistent application session state."""
    if "engine" not in st.session_state:
        loader = CaseLoader()
        memory = MemoryManager(":memory:")
        engine = GameEngine(case_loader=loader, memory_manager=memory)
        client = SarvamClient()
        analyzer = ContradictionAnalyzer(engine.case_data)
        validator = GroundTruthValidator(engine.case_data)

        # Initialize agents for all suspects
        agents: Dict[str, SuspectAgent] = {}
        for s in engine.case_data.suspects:
            agents[s.id] = SuspectAgent(
                suspect=s,
                case_data=engine.case_data,
                memory_manager=memory,
                contradiction_analyzer=analyzer,
                validator=validator,
                sarvam_client=client,
            )

        st.session_state.loader = loader
        st.session_state.memory = memory
        st.session_state.engine = engine
        st.session_state.client = client
        st.session_state.agents = agents
        st.session_state.gm = GameMasterAgent(engine.case_data)
        st.session_state.benchmark_results = None
        st.session_state.selected_suspect_id = engine.case_data.suspects[0].id


init_session_state()

engine: GameEngine = st.session_state.engine
case_data = engine.case_data
gm: GameMasterAgent = st.session_state.gm

# Sidebar controls
with st.sidebar:
    st.markdown("### 🕵️ MurderBox Dossier")
    st.markdown(f"**Case:** {case_data.title}")
    st.markdown(f"**Victim:** {case_data.victim_name} ({case_data.victim_age})")
    st.markdown(f"**Time:** {case_data.incident_time}")
    st.markdown("---")

    metrics = gm.get_progress_metrics(engine.state)
    st.markdown("#### Investigation Status")
    st.write(f"📁 Clues Found: **{metrics['evidence_discovered']}**")
    st.write(f"👥 Questioned: **{metrics['suspects_questioned']}**")
    st.write(f"⚠️ Contradictions: **{metrics['contradictions_caught']}**")
    st.write(f"⏳ Turns Left: **{metrics['turns_remaining']}**")
    st.progress(metrics["investigation_readiness"] / 100.0)

    st.markdown("---")
    st.info(f"💡 **Next Lead:**\n{gm.get_next_lead_hint(engine.state)}")

    st.markdown("---")
    if st.button("🔄 Reset Investigation", use_container_width=True):
        engine.reset_game()
        init_session_state()
        st.session_state.benchmark_results = None
        st.rerun()

# Top Header
ui.render_header(case_data.title, case_data.subtitle)
ui.render_investigation_meter(metrics)

# Main Navigation Tabs
tab_briefing, tab_suspects, tab_interrogate, tab_scene, tab_notebook, tab_accuse, tab_benchmark = st.tabs([
    "🔍 Case Briefing",
    "👥 Suspects Dossier",
    "🎙️ Interrogation Room",
    "🗝️ Crime Scene Search",
    "📓 Detective's Notebook",
    "⚖️ Accusation & Verdict",
    "📊 Research Benchmark",
])

# ==============================================================================
# TAB 1: CASE BRIEFING
# ==============================================================================
with tab_briefing:
    st.markdown("### 📂 Case Summary & Incident Report")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(
            f"""
            <div class="noir-card">
                <h3 style="color: #f0f6fc; margin-top: 0;">The Crime at Vance Manor</h3>
                <p>{case_data.synopsis}</p>
                <div style="background: #0d1117; padding: 12px; border-radius: 6px; margin-top: 10px;">
                    <p style="margin: 0; color: #ff9999;"><strong>Cause of Death:</strong> {case_data.cause_of_death}</p>
                    <p style="margin: 4px 0 0 0; color: #8b949e;"><strong>Estimated Time of Death:</strong> 10:14 PM (Broken pocket watch)</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("#### 🕒 Initial Chronology of Events")
        for ev in case_data.timeline:
            marker = "🔴" if ev.is_key_time else "⚪"
            verified_tag = "✓ Verified" if ev.verified else "Unconfirmed"
            st.markdown(f"**{marker} {ev.time_str}** — {ev.description} `[{verified_tag}]`")

    with col2:
        st.markdown(
            f"""
            <div class="noir-card noir-card-gold">
                <h3 style="color: #d4af37; margin-top: 0;">Victim Dossier</h3>
                <h4>{case_data.victim_name}, {case_data.victim_age}</h4>
                <p style="font-size: 0.95rem;">{case_data.victim_bio}</p>
                <hr style="border-color: #30363d;"/>
                <p style="font-size: 0.9rem; color: #8b949e;">
                    Found locked from within his personal study. The crystal decanter was delivered at 9:30 PM.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ==============================================================================
# TAB 2: SUSPECTS DOSSIER
# ==============================================================================
with tab_suspects:
    st.markdown("### 👥 Person of Interest Dossiers")
    st.caption("Review suspect biographies, reported relationships to the victim, and initial statements.")

    cols = st.columns(2)
    for idx, s in enumerate(case_data.suspects):
        turns_with_suspect = len([t for t in engine.state.interrogation_turns if t.suspect_id == s.id])
        with cols[idx % 2]:
            ui.render_suspect_card(s, times_questioned=turns_with_suspect)
            if st.button(f"🎙️ Question {s.name}", key=f"btn_nav_{s.id}"):
                st.session_state.selected_suspect_id = s.id
                st.info(f"Selected {s.name}. Switch to the 'Interrogation Room' tab to interrogate.")


# ==============================================================================
# TAB 3: INTERROGATION ROOM
# ==============================================================================
with tab_interrogate:
    st.markdown("### 🎙️ Interrogation Room")

    suspect_options = {s.id: f"{s.avatar_emoji} {s.name} — {s.role}" for s in case_data.suspects}
    current_suspect_id = st.selectbox(
        "Select Suspect to Question:",
        options=list(suspect_options.keys()),
        format_func=lambda x: suspect_options[x],
        index=list(suspect_options.keys()).index(st.session_state.selected_suspect_id),
    )
    st.session_state.selected_suspect_id = current_suspect_id
    active_suspect = case_data.get_suspect(current_suspect_id)
    agent = st.session_state.agents[current_suspect_id]

    st.markdown("---")

    # Present Clues Dropdown
    discovered_clues = engine.get_discovered_evidence()
    clue_options = {e.id: f"{e.name} ({e.category})" for e in discovered_clues}

    selected_clue_ids = st.multiselect(
        "📁 Present Evidence During this Question (Optional):",
        options=list(clue_options.keys()),
        format_func=lambda x: clue_options[x],
        help="Confront the suspect with physical or documentary clues to pressure them and test their alibi.",
    )

    # Question Input
    preset_questions = [
        "Where were you between 9:30 PM and 10:30 PM?",
        "Did you enter Arthur Vance's study tonight?",
        "What was your argument with Arthur about earlier this evening?",
        "Did you touch Arthur's scotch decanter or tamper with it?",
        "Someone saw you outside in the rain near the study patio!",
        "Confess to Arthur Vance's murder!",
    ]

    selected_preset = st.selectbox("Quick Inquiries:", ["-- Select or type a custom question below --"] + preset_questions)

    question_text = st.text_input(
        "Your Interrogation Question:",
        value=selected_preset if selected_preset != "-- Select or type a custom question below --" else "",
        placeholder="e.g. Why were your bespoke brogue footprints found on the study patio?",
    )

    if st.button("⚡ Ask Question", type="primary"):
        if question_text.strip():
            presented_items = [case_data.get_evidence(eid) for eid in selected_clue_ids if case_data.get_evidence(eid)]
            discovered_items = engine.get_discovered_evidence()

            with st.spinner(f"Interrogating {active_suspect.name}..."):
                turn = agent.interrogate(
                    question=question_text.strip(),
                    presented_evidence=presented_items,
                    discovered_evidence=discovered_items,
                )
                engine.record_turn(turn)
            st.rerun()
        else:
            st.warning("Please enter a question for the suspect.")

    # Interrogation History
    suspect_turns = [t for t in engine.state.interrogation_turns if t.suspect_id == current_suspect_id]

    st.markdown("#### 💬 Dialogue Transcript")
    if not suspect_turns:
        st.markdown(
            f'<div class="noir-card"><p style="color: #8b949e; font-style: italic;">{active_suspect.initial_statement}</p></div>',
            unsafe_allow_html=True,
        )
    else:
        for turn in reversed(suspect_turns):
            ui.render_dialogue_turn(turn, active_suspect.name)


# ==============================================================================
# TAB 4: CRIME SCENE SEARCH & EVIDENCE LOCKER
# ==============================================================================
with tab_scene:
    st.markdown("### 🗝️ Manor Crime Scene & Evidence Locker")
    st.caption("Search manor rooms to uncover physical evidence, forensic specimens, and financial records.")

    st.markdown("#### 📍 Explore Estate Locations")
    loc_cols = st.columns(3)
    for i, loc in enumerate(case_data.locations):
        is_searched = loc.id in engine.state.explored_location_ids
        with loc_cols[i % 3]:
            st.markdown(
                f"""
                <div class="noir-card">
                    <h4 style="color: #f0f6fc; margin: 0;">🏛️ {loc.name}</h4>
                    <p style="color: #8b949e; font-size: 0.85rem; margin-top: 4px;">{loc.description}</p>
                    <p style="font-size: 0.8rem; color: {'#38bdf8' if is_searched else '#8b0000'};">
                        {'✓ Searched' if is_searched else '⚪ Unsearched'} ({len(loc.evidence_ids)} items)
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if not is_searched:
                if st.button(f"🔍 Search {loc.name}", key=f"search_{loc.id}"):
                    found = engine.search_location(loc.id)
                    st.success(f"Discovered {len(found)} clues in {loc.name}!")
                    st.rerun()

    st.markdown("---")
    st.markdown("#### 🗄️ Evidence Locker (Discovered Clues)")

    discovered = engine.get_discovered_evidence()
    if not discovered:
        st.info("No clues have been discovered yet. Search manor locations above to recover evidence.")
    else:
        for ev in discovered:
            ui.render_evidence_card(ev)


# ==============================================================================
# TAB 5: DETECTIVE'S NOTEBOOK
# ==============================================================================
with tab_notebook:
    st.markdown("### 📓 Detective's Notebook & Contradiction Board")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### ⚠️ Caught Contradictions & Lies")
        if not engine.state.detected_contradictions:
            st.info("No contradictions detected yet. Interrogate suspects and present conflicting evidence to break their alibis.")
        else:
            for contra in engine.state.detected_contradictions:
                ui.render_contradiction_banner(contra)

    with col2:
        st.markdown("#### 📝 Case Notes")
        new_note = st.text_area("Record an Observation or Hypothesis:", placeholder="e.g. Dr. Croft's brogues match the patio footprint...")
        if st.button("📌 Add Note"):
            if new_note.strip():
                engine.add_notebook_note(new_note.strip())
                st.success("Note recorded.")
                st.rerun()

        if engine.state.notebook_notes:
            for note in reversed(engine.state.notebook_notes):
                st.markdown(f"- ✍️ {note}")


# ==============================================================================
# TAB 6: ACCUSATION & CASE RESOLUTION
# ==============================================================================
with tab_accuse:
    st.markdown("### ⚖️ The Final Accusation")
    st.caption("Assemble your case: name the killer, specify their motive, present the supporting physical evidence, and deliver your indictment.")

    with st.form("accusation_form"):
        suspect_map = {s.id: f"{s.name} ({s.role})" for s in case_data.suspects}
        accused_id = st.selectbox("1. The Accused Killer:", options=list(suspect_map.keys()), format_func=lambda x: suspect_map[x])

        motive_options = [
            "Clinical trial fraud exposure & imminent criminal indictment",
            "Inheritance and avoiding disinheritance under pending divorce",
            "Covering up $14M company embezzlement",
            "Revenge for stolen botanical patents and ruined scientific career",
            "Retaliation for nephew's dismissal and eviction",
            "Hiding insider leaks to hedge funds",
        ]
        selected_motive = st.selectbox("2. Murder Motive:", options=motive_options)

        discovered = engine.get_discovered_evidence()
        evidence_map = {e.id: f"{e.name} ({e.category})" for e in discovered}
        selected_evidence = st.multiselect(
            "3. Primary Supporting Evidence (Select 3-5 items):",
            options=list(evidence_map.keys()),
            format_func=lambda x: evidence_map[x],
        )

        closing_statement = st.text_area(
            "4. Detective's Closing Indictment / Rationale:",
            placeholder="Explain how the crime was committed and how the evidence pieces together...",
        )

        submit_accusation = st.form_submit_button("🔨 Deliver Final Indictment & Issue Arrest Warrant", type="primary")

    if submit_accusation:
        submission = AccusationSubmission(
            accused_suspect_id=accused_id,
            selected_motive=selected_motive,
            selected_evidence_ids=selected_evidence,
            closing_rationale=closing_statement,
        )
        verdict_result = engine.submit_accusation(submission)
        st.session_state.verdict_result = verdict_result

    if "verdict_result" in st.session_state and st.session_state.verdict_result:
        ui.render_verdict_card(st.session_state.verdict_result)


# ==============================================================================
# TAB 7: RESEARCH & BENCHMARK LAB
# ==============================================================================
with tab_benchmark:
    st.markdown("### 📊 Research & Agent Benchmark Lab")
    st.caption(
        "Empirical evaluation comparing three autonomous agent architectures across 22 standardized mystery scenarios."
    )

    st.markdown(
        """
        <div class="noir-card">
            <h4>Experimental Configurations:</h4>
            <ul>
                <li><strong>Configuration 1 (Baseline):</strong> Stateless LLM / prompt without memory or boundary protection.</li>
                <li><strong>Configuration 2 (Memory):</strong> SQLite persistent memory of dialogue history.</li>
                <li><strong>Configuration 3 (Full Architecture):</strong> SQLite persistent memory + Ground-Truth Validator + Contradiction Analyzer.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🚀 Run Full Benchmark Experiment (22 Scenarios)", type="primary"):
        with st.spinner("Executing benchmark across all 3 agent architectures..."):
            benchmark_engine = AgentBenchmarkEngine(st.session_state.loader)
            benchmark_results = benchmark_engine.run_benchmark()
            st.session_state.benchmark_results = benchmark_results
        st.success("Benchmark completed!")

    if st.session_state.benchmark_results:
        metrics_dict = st.session_state.benchmark_results["metrics"]

        # Prepare summary table
        rows = []
        for name, m in metrics_dict.items():
            rows.append({
                "Architecture": name,
                "Passed": f"{m.passed_scenarios}/{m.total_scenarios}",
                "Consistency %": f"{m.consistency_rate}%",
                "Leakage % (lower=better)": f"{m.leakage_rate}%",
                "Contra Precision %": f"{m.contradiction_precision}%",
                "Contra Recall %": f"{m.contradiction_recall}%",
                "Contra F1 %": f"{m.contradiction_f1}%",
                "Grounding %": f"{m.grounding_accuracy}%",
                "Overall Score": f"{m.overall_score} / 100",
            })
        df_summary = pd.DataFrame(rows)
        st.dataframe(df_summary, use_container_width=True)

        st.markdown("#### 🔬 Detailed Scenario Results (Full Architecture)")
        full_res = st.session_state.benchmark_results["raw_results"].get(
            "Full Architecture (Memory + Evidence + Validator)", []
        )
        detail_rows = []
        for r in full_res:
            detail_rows.append({
                "ID": r["scenario_id"],
                "Category": r["category"],
                "Title": r["title"],
                "Status": "✅ PASS" if r["passed"] else "❌ FAIL",
                "Contra Expected": r["expected_contra"],
                "Contra Detected": r["actual_contra"],
                "Notes": ", ".join(r["failure_reasons"]) if r["failure_reasons"] else "Meets criteria",
            })
        df_detail = pd.DataFrame(detail_rows)
        st.dataframe(df_detail, use_container_width=True)
