# Implementation Plan: MurderBox — Interactive AI Murder Mystery Powered by Autonomous Agents

MurderBox is an interactive mystery game and research framework where players take on the role of a detective investigating a murder by interrogating AI-powered suspects. The system integrates Sarvam AI's chat completion models with a deterministic Python game engine, persistent character memory (SQLite), an evidence and contradiction analyzer, a ground-truth validator to prevent hallucination/leakage, a final accusation and case resolution system, a research benchmark module comparing three agent configurations, and an atmospheric noir Streamlit detective dashboard.

## User Review Required

> [!IMPORTANT]
> **Workspace Location**: The project will be initialized in `C:\Users\Owner\.gemini\antigravity\scratch\murderbox`. You can set this directory as your active workspace in Antigravity or open it in your editor.
>
> **Sarvam AI API Key**: The system connects to Sarvam AI (`https://api.sarvam.ai/v1/chat/completions`) using the `SARVAM_API_KEY` environment variable. A high-fidelity, deterministic Mock Provider is included out-of-the-box so that you can play the full game, run unit tests, and conduct evaluation benchmarks immediately without requiring an active key.

---

## 1. Case Mystery Design: "The Vance Manor Mystery"

We design an airtight, classic-noir whodunit: **"The Death of Arthur Vance"**

- **Victim**: Arthur Vance (62), billionaire biomedical tycoon and art collector.
- **Crime**: Found dead in his locked study at 11:30 PM on a stormy night, holding a broken vintage pocket watch stopped at 10:14 PM. Cause of death: respiratory paralysis from a rare alkaloid poison (*Aconitum ferox* / Monkshood extract) slipped into his nightly scotch.
- **The 6 Suspects**:
  1. **Elena Vance** (Estranged Wife, 45): Cold, poised, elegant. Motive: Pending divorce will disinherit her if finalized tomorrow; stands to inherit $80M under the current will. Private secret: Sent an encrypted text to her divorce attorney at 9:45 PM. Alibi: Reading in the drawing room.
  2. **Dr. Julian Croft** (Personal Physician, 52): Calm, intellectual, evasive. Motive: Arthur recently audited his private clinic and discovered forged experimental drug trials. Private secret: Arthur threatened to revoke his medical license and report him to the medical board tomorrow morning. Alibi: In the guest wing organizing medicine kits.
  3. **Marcus Sterling** (Business Partner / COO, 38): Brash, charismatic, defensive. Motive: Secretly embezzled $14M from Vance Biometrics; Arthur had summoned him to demand his resignation. Private secret: Attempted to break into the study safe earlier that evening. Alibi: Drinking on the terrace.
  4. **Clara Dupont** (Head Housekeeper, 58): Observant, protective, tight-lipped. Motive: Arthur fired her nephew two days ago and threatened eviction. Private secret: Entered the study at 9:30 PM to deliver the decanter of 25-year-old scotch, but found Arthur arguing with someone. Alibi: Cleaning in the kitchen pantry.
  5. **Vincent Reed** (Disgraced Research Chemist / Groundsman, 41): Bitter, reclusive, nervous. Motive: Arthur stole his patent on synthesized aconite alkaloids and ruined his academic career. Private secret: Cultivates monkshood in the manor's conservatory greenhouse. Alibi: Walking in the rose garden in the rain.
  6. **Evelyn Cross** (Private Secretary, 29): Sharp, methodical, anxious. Motive: Arthur discovered she was leaking insider confidential memos to a hedge fund. Private secret: Has a key to the study's side entrance and saw the culprit slipping away. Alibi: Filing papers in the library.
- **The Culprit**: **Dr. Julian Croft**
  - **Motive**: Destruction of his career and imminent criminal indictment for medical fraud.
  - **Method**: Syringe delivery of concentrated Monkshood alkaloid directly into Arthur's decanter stopper during his routine 9:45 PM consultation, knowing Arthur took his scotch precisely at 10:00 PM.
  - **Key Physical & Forensic Clues**:
    - *Toxicology Report*: Confirms concentrated aconitine toxicity.
    - *Scotch Decanter*: Traces of needle puncture on the silicone inner seal.
    - *Doctor's Medical Bag*: Missing ampoule of aconitine reagent and discarded sterile syringe wrapper.
    - *Audit Dossier*: Arthur's handwritten audit findings exposing Julian's forged signatures.
    - *Muddy Footprints*: Matching bespoke orthopedic leather brogues near the study's patio door.

---

## 2. Architecture & Component Design

```
murderbox/
├── data/
│   └── cases/
│       └── the_vance_mystery.json       # Authoritative case data (ground truth, suspects, clues, locations)
├── murderbox/
│   ├── models/
│   │   ├── case.py                      # Pydantic schemas: SuspectProfile, EvidenceItem, TimelineEvent, CaseData
│   │   ├── dialogue.py                  # InterrogationTurn, StatementClaim, ContradictionModel
│   │   └── investigation.py             # InvestigationState, AccusationSubmission, AccusationResult
│   ├── engine/
│   │   ├── case_loader.py               # Case JSON validator and loader
│   │   ├── game_engine.py               # Deterministic state machine (locations, clues, turns, scoring)
│   │   ├── memory_manager.py            # SQLite persistent memory for character claims and chat turns
│   │   ├── contradiction_analyzer.py    # Statement vs Statement, Statement vs Evidence, Statement vs Fact
│   │   └── validator.py                 # Ground-truth validator & information boundary guard
│   ├── llm/
│   │   ├── sarvam_client.py             # Sarvam AI chat completion client (v1 API with retries, timeout, session affinity)
│   │   ├── prompt_builder.py            # Suspect system prompt generator with strict knowledge boundaries
│   │   └── mock_provider.py             # Deterministic fallback provider for offline play & test suites
│   ├── agents/
│   │   ├── suspect_agent.py             # Agent orchestrator coordinating memory, LLM, and validator
│   │   └── game_master.py               # Hints, progression tracking, investigation notebook updates
│   ├── evaluation/
│   │   ├── test_dataset.py              # Labelled benchmark dataset (consistency, contradictions, leakages)
│   │   ├── metrics.py                   # Evaluation metrics (precision, recall, leakage rate, F1)
│   │   └── benchmark.py                 # Comparative experiment engine (Baseline vs Memory vs Memory+Evidence)
│   └── ui/
│       ├── app.py                       # Streamlit application with rich tabbed UI
│       ├── components.py                # Reusable UI widgets: Evidence cards, suspect dossiers, contradiction badges
│       └── styles.py                    # Noir detective styling (custom CSS)
├── tests/
│   ├── test_case_loader.py
│   ├── test_game_engine.py
│   ├── test_memory_manager.py
│   ├── test_contradiction_analyzer.py
│   ├── test_sarvam_client.py
│   ├── test_accusation.py
│   └── test_evaluation.py
├── requirements.txt
├── README.md
└── .env.example
```

---

## 3. Key Subsystems Implementation Details

### A. Sarvam AI Client & Information Boundary Protection
- Endpoint: `https://api.sarvam.ai/v1/chat/completions` (OpenAI-compatible format, models: `sarvam-105b` / `sarvam-105b-conversations`).
- Strict prompt partitioning: The suspect prompt receives ONLY:
  - Persona, communication tone, background.
  - Public knowledge + Authorized private knowledge for that specific character.
  - Retrieved past memories from previous interrogations with this suspect.
  - Discovered evidence that the player explicitly presents during the turn.
- The prompt explicitly **excludes** the ground truth, culprit identity (unless the suspect IS the culprit, in which case they possess deceptive instructions and defense mechanisms), and unauthorized secrets of other suspects.
- Response Validator: Scans generated text for unauthorized leakage or attempt to redefine game facts. If an invalid claim is made, it falls back to a guarded in-character deflection.

### B. Memory Manager (SQLite-backed)
- Stores all interrogation turns: `turn_id`, `suspect_id`, `user_query`, `presented_evidence_ids`, `suspect_response`, `timestamp`.
- Extracts and indexes factual claims made by the suspect: `claim_text`, `entity`, `claimed_time`, `claimed_location`, `status` (unverified, verified, contradicted).
- Retrieves relevant context when the player re-questions a suspect (recalling what was discussed earlier, preventing flip-flopping).

### C. Contradiction Detection Engine
- Evaluates statements against 4 contradiction vectors:
  1. **Self-Contradiction**: Suspect changes alibi or denies a statement they previously uttered.
  2. **Evidence Contradiction**: Suspect claims an alibi or action that directly conflicts with a verified physical clue (e.g., claiming they never left the drawing room when their footprints were discovered on the patio).
  3. **Inter-Suspect Conflict**: Suspect A's account of a specific event conflicts with Suspect B's verified account.
  4. **Ground-Truth Conflict**: Suspect states a false fact about crime scene geography or baseline verifiable facts.
- Distinguishes between:
  - Factual contradiction (Severity: High).
  - Plausible uncertainty or evasion (Severity: Low / Ambiguous).

### D. Evidence Discovery & Crime Scene Investigation
- Manor map with searchable locations:
  - *Study (Crime Scene)*
  - *Library*
  - *Conservatory & Greenhouse*
  - *Drawing Room*
  - *Dr. Croft's Guest Suite*
  - *Wine Cellar & Kitchen Pantry*
- Searching locations yields physical clues based on investigation progress and inspection. Clues can be inspected in the Evidence Board and presented directly to suspects during interrogation.

### E. Final Accusation & Scoring Engine
- Player selects:
  1. The Accused Suspect (e.g., Dr. Julian Croft).
  2. The Murder Motive (e.g., Fraud Exposure & Medical Blackmail).
  3. Primary Supporting Clues (select up to 3-4 key evidence items).
  4. Detective's Closing Statement / Rationale.
- Engine evaluates:
  - Culprit Match: 40 points
  - Motive Match: 25 points
  - Evidence Strength: 25 points
  - Uncovered Contradictions bonus: 10 points
  - Verdict tiers: *Master Detective (90-100%)*, *Competent Sleuth (70-89%)*, *Flawed Deduction (40-69%)*, *Wrongful Arrest (<40%)*.
- Generates a complete Case Resolution breakdown detailing the real sequence of events, what clues the player caught or missed, and the culprit's full confession.

### F. Research & Evaluation Benchmark (PRD Section 12)
- Implements a repeatable experiment framework comparing 3 configurations:
  1. **Configuration 1 (Baseline)**: Stateless LLM-driven suspects (no persistent memory, prompt only).
  2. **Configuration 2 (Memory)**: Suspects with SQLite persistent memory and recall of previous turns.
  3. **Configuration 3 (Memory + Evidence Validation)**: Suspects with persistent memory, evidence-aware prompting, and ground-truth boundary enforcement.
- Test Suite contains 20+ labelled benchmark scenarios testing:
  - Character Consistency (does the suspect remember their alibi across 3 turns?)
  - Leakage Prevention (does the suspect resist trick questions probing other suspects' secrets or the hidden murder method?)
  - Contradiction Detection Precision & Recall (can the analyzer correctly flag conflicting claims?)
  - Culprit Identification Grounding.
- Generates summary statistics and comparison tables.

### G. Streamlit Web Interface
- Atmospheric dark detective theme.
- Tabs:
  - 🔍 **Case Briefing**: Crime synopsis, victim bio, known timeline, investigation meter.
  - 👥 **Suspects Dossier**: Character cards with portraits, relationships, alibis, interrogation status.
  - 🎙️ **Interrogation Room**: Live dialogue interface with suspect selection, evidence presentation dropdown, chat transcript, claim analysis badges, and real-time contradiction alerts.
  - 🗝️ **Crime Scene Search & Evidence Locker**: Explore manor locations, inspect discovered clues, track undiscovered items.
  - 📓 **Detective's Notebook**: Chronological log of recorded claims, verified facts, and detected contradictions.
  - ⚖️ **Accusation & Verdict**: Accuse the killer, submit evidence, and view the case resolution cinematic narrative.
  - 📊 **Research & Benchmark Lab**: Run the 3-model evaluation benchmark live, display comparative metrics and charts.

---

## 4. Verification Plan

### Automated Testing (`pytest`)
- Run full automated test suite:
  ```powershell
  pytest tests/ -v
  ```
- Tests cover:
  1. `test_case_loader.py`: JSON schema validation, completeness of clues, suspects, timeline, solution.
  2. `test_game_engine.py`: Clue discovery, interrogation state transitions, turn counting.
  3. `test_memory_manager.py`: SQLite turn saving, claim extraction, memory retrieval by suspect.
  4. `test_contradiction_analyzer.py`: Self-contradictions, evidence conflicts, cross-suspect conflicts.
  5. `test_sarvam_client.py`: Mock provider behavior, payload structure, error recovery.
  6. `test_accusation.py`: Perfect solve vs partial solve vs wrong culprit scoring.
  7. `test_evaluation.py`: Running benchmark suite across all 3 agent configurations.

### Manual & UI Verification
- Launch the Streamlit application:
  ```powershell
  streamlit run murderbox/ui/app.py
  ```
- Verify:
  - Interrogating multiple suspects preserves conversational memory.
  - Searching a room (e.g. Conservatory) discovers the monkshood clue.
  - Presenting the "Medical Bag" or "Scotch Decanter" to Dr. Croft triggers a defensive contradiction.
  - Submitting a correct accusation unlocks the "Master Detective" resolution screen.
  - Running the Benchmark tab executes the evaluation scenarios and renders comparative performance metrics.
