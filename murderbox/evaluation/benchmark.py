"""Comparative evaluation benchmark engine running 3 agent configurations."""

from typing import List, Dict, Any, Optional
from murderbox.models.case import CaseData, SuspectProfile, EvidenceItem
from murderbox.engine.case_loader import CaseLoader
from murderbox.engine.memory_manager import MemoryManager
from murderbox.engine.contradiction_analyzer import ContradictionAnalyzer
from murderbox.engine.validator import GroundTruthValidator
from murderbox.llm.sarvam_client import SarvamClient
from murderbox.agents.suspect_agent import SuspectAgent
from murderbox.evaluation.test_dataset import BENCHMARK_SCENARIOS, BenchmarkScenario
from murderbox.evaluation.metrics import BenchmarkMetrics, calculate_evaluation_metrics


class AgentBenchmarkEngine:
    """Executes comparative evaluation across Baseline, Memory, and Full Memory+Evidence architectures."""

    def __init__(self, case_loader: Optional[CaseLoader] = None):
        self.loader = case_loader or CaseLoader()
        self.case_data: CaseData = self.loader.get_case()

    def run_benchmark(self) -> Dict[str, Any]:
        """Runs the entire benchmark dataset against the 3 configurations."""
        configs = [
            ("Baseline (Stateless)", self._run_baseline),
            ("Memory Only (SQLite)", self._run_memory_only),
            ("Full Architecture (Memory + Evidence + Validator)", self._run_full_architecture),
        ]

        metrics_by_config: Dict[str, BenchmarkMetrics] = {}
        raw_results_by_config: Dict[str, List[Dict[str, Any]]] = {}

        for config_name, runner_fn in configs:
            results = runner_fn()
            metrics = calculate_evaluation_metrics(config_name, results)
            metrics_by_config[config_name] = metrics
            raw_results_by_config[config_name] = results

        return {
            "metrics": metrics_by_config,
            "raw_results": raw_results_by_config,
            "total_scenarios": len(BENCHMARK_SCENARIOS),
        }

    def _evaluate_scenario_response(
        self,
        scenario: BenchmarkScenario,
        response_text: str,
        contradictions_found: List[Any],
    ) -> Dict[str, Any]:
        """Evaluates whether an individual scenario passed or failed."""
        lower = response_text.lower()
        passed = True
        failure_reasons = []

        # Check required substrings
        for req in scenario.required_substrings:
            if req.lower() not in lower:
                passed = False
                failure_reasons.append(f"Missing required phrase: '{req}'")

        # Check forbidden substrings
        for forb in scenario.forbidden_substrings:
            if forb.lower() in lower:
                passed = False
                failure_reasons.append(f"Contains forbidden leak: '{forb}'")

        # Check contradiction detection
        actual_contra = len(contradictions_found) > 0
        if scenario.should_detect_contradiction and not actual_contra:
            passed = False
            failure_reasons.append("Failed to detect expected contradiction.")

        return {
            "scenario_id": scenario.id,
            "category": scenario.category,
            "title": scenario.title,
            "passed": passed,
            "failure_reasons": failure_reasons,
            "expected_contra": scenario.should_detect_contradiction,
            "actual_contra": actual_contra,
            "response_snippet": response_text[:120],
        }

    def _run_baseline(self) -> List[Dict[str, Any]]:
        """Config 1: Stateless LLM/mock without memory or boundary validation."""
        results = []
        client = SarvamClient(force_mock=True)

        for sc in BENCHMARK_SCENARIOS:
            suspect = self.case_data.get_suspect(sc.suspect_id)
            if not suspect:
                continue

            # In baseline: no evidence is presented to prompt, no memory context, no validator
            gen = client.generate_suspect_response(
                suspect=suspect,
                user_query=sc.prompt,
                presented_evidence=[],
                dialogue_history=None,
            )
            raw = gen["text"]

            # If it's a leakage test probing confessions, baseline often hallucinates or gives generic text
            if sc.category == "leakage" and "Confess" in sc.prompt:
                # Baseline vulnerability simulation
                pass

            # No contradiction analyzer attached to baseline
            res = self._evaluate_scenario_response(sc, raw, contradictions_found=[])
            results.append(res)

        return results

    def _run_memory_only(self) -> List[Dict[str, Any]]:
        """Config 2: Includes SQLite memory persistence, but lacks validator and contradiction rules."""
        results = []
        mem = MemoryManager(":memory:")
        client = SarvamClient(force_mock=True)

        for sc in BENCHMARK_SCENARIOS:
            suspect = self.case_data.get_suspect(sc.suspect_id)
            if not suspect:
                continue

            history = mem.get_formatted_dialogue_context(suspect.id, limit=3)
            # Memory config passes history, but no presented clues or validator
            gen = client.generate_suspect_response(
                suspect=suspect,
                user_query=sc.prompt,
                presented_evidence=[],
                dialogue_history=history,
            )
            raw = gen["text"]

            res = self._evaluate_scenario_response(sc, raw, contradictions_found=[])
            results.append(res)

        return results

    def _run_full_architecture(self) -> List[Dict[str, Any]]:
        """Config 3: Full system with SQLite memory, ground-truth validator, and contradiction analyzer."""
        results = []
        mem = MemoryManager(":memory:")
        analyzer = ContradictionAnalyzer(self.case_data)
        validator = GroundTruthValidator(self.case_data)
        client = SarvamClient(force_mock=True)

        for sc in BENCHMARK_SCENARIOS:
            suspect = self.case_data.get_suspect(sc.suspect_id)
            if not suspect:
                continue

            agent = SuspectAgent(
                suspect=suspect,
                case_data=self.case_data,
                memory_manager=mem,
                contradiction_analyzer=analyzer,
                validator=validator,
                sarvam_client=client,
            )

            presented_clues = [
                self.case_data.get_evidence(eid)
                for eid in sc.presented_evidence_ids
                if self.case_data.get_evidence(eid) is not None
            ]

            turn = agent.interrogate(
                question=sc.prompt,
                presented_evidence=presented_clues,
                discovered_evidence=presented_clues,
            )

            res = self._evaluate_scenario_response(sc, turn.response, turn.contradictions_found)
            results.append(res)

        return results
