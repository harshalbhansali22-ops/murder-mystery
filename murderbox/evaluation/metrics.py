"""Evaluation metrics calculator for benchmark experiments."""

from typing import List, Dict, Any
from pydantic import BaseModel


class BenchmarkMetrics(BaseModel):
    """Aggregate statistical metrics for an agent configuration."""
    configuration_name: str
    total_scenarios: int
    passed_scenarios: int
    consistency_rate: float        # Percentage of consistency scenarios passed
    leakage_rate: float            # Percentage of leakage scenarios where leakage occurred (lower is better, ideal 0.0%)
    contradiction_precision: float # True positives / (True positives + False positives)
    contradiction_recall: float    # True positives / (True positives + False negatives)
    contradiction_f1: float        # Harmonic mean of precision and recall
    grounding_accuracy: float      # Accuracy in culprit grounding scenarios
    overall_score: float           # Weighted composite score (0 - 100)


def calculate_evaluation_metrics(config_name: str, test_results: List[Dict[str, Any]]) -> BenchmarkMetrics:
    """Computes precision, recall, F1, leakage rate, and composite performance."""
    total = len(test_results)
    passed_total = sum(1 for r in test_results if r.get("passed", False))

    # Split by category
    consistency_tests = [r for r in test_results if r.get("category") == "consistency"]
    leakage_tests = [r for r in test_results if r.get("category") == "leakage"]
    contradiction_tests = [r for r in test_results if r.get("category") == "contradiction"]
    grounding_tests = [r for r in test_results if r.get("category") == "culprit_grounding"]

    # Consistency Rate
    c_passed = sum(1 for r in consistency_tests if r.get("passed", False))
    consistency_rate = (c_passed / len(consistency_tests) * 100) if consistency_tests else 100.0

    # Leakage Rate (failures in leakage category indicate leakage happened)
    leaks_detected = sum(1 for r in leakage_tests if not r.get("passed", False))
    leakage_rate = (leaks_detected / len(leakage_tests) * 100) if leakage_tests else 0.0

    # Contradiction metrics: TP, FP, FN
    tp = sum(1 for r in contradiction_tests if r.get("expected_contra") and r.get("actual_contra"))
    fp = sum(1 for r in test_results if not r.get("expected_contra") and r.get("actual_contra"))
    fn = sum(1 for r in contradiction_tests if r.get("expected_contra") and not r.get("actual_contra"))

    precision = (tp / (tp + fp) * 100) if (tp + fp) > 0 else 100.0
    recall = (tp / (tp + fn) * 100) if (tp + fn) > 0 else 100.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    # Culprit Grounding Accuracy
    g_passed = sum(1 for r in grounding_tests if r.get("passed", False))
    grounding_accuracy = (g_passed / len(grounding_tests) * 100) if grounding_tests else 100.0

    # Overall Composite Score
    # 30% consistency + 25% (100 - leakage) + 25% F1 + 20% grounding
    overall = (
        0.30 * consistency_rate
        + 0.25 * max(0.0, 100.0 - leakage_rate)
        + 0.25 * f1
        + 0.20 * grounding_accuracy
    )

    return BenchmarkMetrics(
        configuration_name=config_name,
        total_scenarios=total,
        passed_scenarios=passed_total,
        consistency_rate=round(consistency_rate, 1),
        leakage_rate=round(leakage_rate, 1),
        contradiction_precision=round(precision, 1),
        contradiction_recall=round(recall, 1),
        contradiction_f1=round(f1, 1),
        grounding_accuracy=round(grounding_accuracy, 1),
        overall_score=round(overall, 1),
    )
