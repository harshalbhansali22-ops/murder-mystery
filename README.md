# MurderBox: Interactive AI Murder Mystery Powered by Autonomous Agents

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests: 22 Passed](https://img.shields.io/badge/tests-22%20passed-brightgreen.svg)]()
[![Framework: Streamlit](https://img.shields.io/badge/UI-Streamlit-red.svg)](https://streamlit.io/)
[![LLM: Sarvam AI](https://img.shields.io/badge/LLM-Sarvam%20AI-orange.svg)](https://www.sarvam.ai/)

**MurderBox** is an interactive noir murder mystery game and autonomous agent research benchmark. Players assume the role of a lead detective investigating a locked-room murder at **Vance Manor** by exploring estate rooms, uncovering physical and forensic clues, interrogating AI-powered suspects with persistent memory, exposing alibi contradictions, and delivering a final indictment.

---

## 🔍 The Mystery: "The Death of Arthur Vance"

- **Victim**: Arthur Vance (62), billionaire biomedical tycoon and art collector.
- **Incident**: Discovered dead in his locked study at 11:30 PM during a thunderstorm.
- **Time of Death**: Fixed at 10:14 PM by his shattered heirloom pocket watch.
- **Cause of Death**: Sudden cardiovascular collapse caused by a lethal overdose of experimental sedative **Compound V-7** injected through the silicone seal of his nightly scotch decanter.
- **The 6 Suspects**:
  1. 💍 **Elena Vance** (Estranged Wife): Stands to inherit $80M under the current will if the divorce is not finalized.
  2. 🩺 **Dr. Julian Croft** (Personal Physician): Arthur uncovered forged signatures and clinical trial fraud, threatening immediate criminal indictment.
  3. 💼 **Marcus Sterling** (COO, Vance Biometrics): Secretly embezzled $14M from offshore accounts; Arthur summoned him to demand restitution.
  4. 🗝️ **Clara Dupont** (Head Housekeeper): Delivered the fresh decanter at 9:30 PM; Arthur fired and evicted her nephew.
  5. 🌿 **Vincent Reed** (Disgraced Chemist / Groundsman): Arthur stole his botanical sedative patent and ruined his scientific career.
  6. 📑 **Evelyn Cross** (Private Secretary): Leaked confidential boardroom memos; holds a master patio key.

---

## 🏗️ Architecture & Component Design

```
murderbox/
├── data/
│   └── cases/
│       └── the_vance_mystery.json       # Authoritative case ground truth, suspects, clues, locations
├── murderbox/
│   ├── models/
│   │   ├── case.py                      # Pydantic schemas (SuspectProfile, EvidenceItem, TimelineEvent, CaseData)
│   │   ├── dialogue.py                  # InterrogationTurn, StatementClaim, ContradictionModel
│   │   └── investigation.py             # InvestigationState, AccusationSubmission, AccusationResult
│   ├── engine/
│   │   ├── case_loader.py               # Case JSON validator and integrity verifier
│   │   ├── game_engine.py               # Deterministic state machine (locations, clues, turns, scoring)
│   │   ├── memory_manager.py            # Persistent SQLite memory for character claims and chat turns
│   │   ├── contradiction_analyzer.py    # 4-vector contradiction detection engine
│   │   └── validator.py                 # Ground-truth validator & information boundary guard
│   ├── llm/
│   │   ├── sarvam_client.py             # Sarvam AI chat completion client with retry and mock fallback
│   │   ├── prompt_builder.py            # Suspect system prompt generator with strict knowledge boundaries
│   │   └── mock_provider.py             # Deterministic fallback provider for offline play & test suites
│   ├── agents/
│   │   ├── suspect_agent.py             # Agent orchestrator coordinating memory, LLM, and validator
│   │   └── game_master.py               # Hints, progression tracking, and notebook guidance
│   ├── evaluation/
│   │   ├── test_dataset.py              # 22 labelled benchmark scenarios
│   │   ├── metrics.py                   # Precision, recall, F1, leakage rate, consistency rate
│   │   └── benchmark.py                 # Comparative experiment engine (Baseline vs Memory vs Full Architecture)
│   └── ui/
│       ├── app.py                       # Streamlit application with rich 7-tab dashboard
│       ├── components.py                # Reusable UI widgets (evidence cards, suspect dossiers, alert badges)
│       └── styles.py                    # Atmospheric noir detective styling (custom CSS)
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

## 🚀 Quickstart & Setup

### 1. Requirements
Ensure Python 3.11+ is installed.

```powershell
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)
The system includes a deterministic mock provider out-of-the-box so you can play immediately without any API keys.
To connect to live Sarvam AI models:
```powershell
cp .env.example .env
```
Edit `.env`:
```env
SARVAM_API_KEY= sk_e01jh5nm_DKrHUCGmBfR5eczXzxDNCOUx
SARVAM_BASE_URL=https://api.sarvam.ai/v1
SARVAM_MODEL=sarvam-105b
MURDERBOX_MOCK_LLM=false
```

### 3. Launch Streamlit Application
```powershell
streamlit run murderbox/ui/app.py
```
Open your browser to `http://localhost:8501`.

---

## 🧪 Automated Test Suite

Run the full pytest suite:
```powershell
pytest tests/ -v
```
All 22 unit tests test:
- Case schema validation and integrity
- SQLite memory persistence and dialogue formatting
- 4-vector contradiction detection (evidence, self, inter-suspect, ground truth)
- Sarvam AI client and mock fallback behavior
- Accusation scoring tiers (Master Detective down to Wrongful Arrest)
- Full benchmark evaluation across 3 agent architectures

---

## 📊 Research Benchmark Lab

Under the **Research Benchmark** tab in the Streamlit UI, MurderBox runs 22 standardized test scenarios comparing:
1. **Configuration 1 (Baseline)**: Stateless prompt without memory or boundary guards.
2. **Configuration 2 (Memory)**: SQLite persistent dialogue memory.
3. **Configuration 3 (Full Architecture)**: SQLite memory + Ground-Truth Validator + 4-Vector Contradiction Analyzer.

| Architecture | Consistency % | Leakage % | Contra Precision % | Contra Recall % | Contra F1 % | Overall Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline (Stateless)** | 100.0% | 0.0% | 100.0% | 0.0% | 0.0% | 75.0 / 100 |
| **Memory Only (SQLite)** | 100.0% | 0.0% | 100.0% | 0.0% | 0.0% | 75.0 / 100 |
| **Full Architecture** | **100.0%** | **0.0%** | **100.0%** | **100.0%** | **100.0%** | **100.0 / 100** |

---

## ⚖️ Detective Gameplay Rules & Scoring

- **Accusation (100 Points Total)**:
  - Culprit Identification: 40 points
  - Motive Deduction: 25 points
  - Primary Supporting Evidence: 25 points
  - Contradiction Bonus: 10 points
- **Ranks**:
  - 🏆 **Master Detective** (90-100 pts)
  - 🥈 **Competent Sleuth** (70-89 pts)
  - 🥉 **Flawed Deduction** (40-69 pts)
  - ❌ **Wrongful Arrest** (<40 pts)
