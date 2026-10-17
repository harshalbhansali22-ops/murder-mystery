"""Unit tests for the research benchmark module and comparative agent evaluation."""

import pytest
from murderbox.evaluation.benchmark import AgentBenchmarkEngine
from murderbox.evaluation.test_dataset import BENCHMARK_SCENARIOS


def test_benchmark_dataset_integrity():
    assert len(BENCHMARK_SCENARIOS) >= 20
    categories = {s.category for s in BENCHMARK_SCENARIOS}
    assert "consistency" in categories
    assert "leakage" in categories
    assert "contradiction" in categories
    assert "culprit_grounding" in categories


def test_agent_benchmark_execution():
    bench = AgentBenchmarkEngine()
    results = bench.run_benchmark()

    assert "metrics" in results
    assert "raw_results" in results

    metrics = results["metrics"]
    assert "Baseline (Stateless)" in metrics
    assert "Memory Only (SQLite)" in metrics
    assert "Full Architecture (Memory + Evidence + Validator)" in metrics

    baseline = metrics["Baseline (Stateless)"]
    full_arch = metrics["Full Architecture (Memory + Evidence + Validator)"]

    # Full architecture should achieve higher contradiction recall and overall score than baseline
    assert full_arch.contradiction_recall >= baseline.contradiction_recall
    assert full_arch.overall_score >= baseline.overall_score
