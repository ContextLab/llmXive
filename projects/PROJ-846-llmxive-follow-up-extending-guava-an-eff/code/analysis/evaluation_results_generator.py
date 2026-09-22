"""
T037: Evaluation Results Generator

Aggregates evaluation metrics from Symbolic-Guava, Baseline-Guava (Visual), and 
Oracle-Symbolic agents to produce the final evaluation_results.json artifact.

Outputs:
    data/artifacts/evaluation_results.json
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_ARTIFACTS_DIR = PROJECT_ROOT / "data" / "artifacts"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Ensure output directory exists
DATA_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file if it exists, otherwise return None."""
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def calculate_success_rate(outcomes: List[Dict[str, Any]]) -> float:
    """Calculate success rate from a list of TaskOutcome records."""
    if not outcomes:
        return 0.0
    successes = sum(1 for o in outcomes if o.get('success', False))
    return successes / len(outcomes)

def calculate_step_efficiency(outcomes: List[Dict[str, Any]]) -> float:
    """
    Calculate average steps per task for successful tasks.
    Returns 0.0 if no successful tasks exist.
    """
    successful = [o for o in outcomes if o.get('success', False)]
    if not successful:
        return 0.0
    total_steps = sum(o.get('steps_taken', 0) for o in successful)
    return total_steps / len(successful)

def aggregate_failure_distribution(outcomes: List[Dict[str, Any]]) -> Dict[str, int]:
    """Aggregate failure counts by category."""
    distribution: Dict[str, int] = {}
    for outcome in outcomes:
        if not outcome.get('success', False):
            category = outcome.get('failure_category', 'unknown')
            distribution[category] = distribution.get(category, 0) + 1
    return distribution

def load_stats_test_results() -> Optional[Dict[str, Any]]:
    """Load results from the permutation test (T036a)."""
    stats_path = DATA_ARTIFACTS_DIR / "stats_test_results.json"
    return load_json_file(stats_path)

def load_symbolic_outcomes() -> List[Dict[str, Any]]:
    """Load Symbolic-Guava evaluation outcomes."""
    outcomes_path = DATA_PROCESSED_DIR / "symbolic_evaluation_outcomes.json"
    data = load_json_file(outcomes_path)
    return data.get('outcomes', []) if data else []

def load_baseline_outcomes() -> List[Dict[str, Any]]:
    """Load Baseline-Guava (Visual) evaluation outcomes."""
    outcomes_path = DATA_PROCESSED_DIR / "baseline_evaluation_outcomes.json"
    data = load_json_file(outcomes_path)
    return data.get('outcomes', []) if data else []

def load_oracle_outcomes() -> List[Dict[str, Any]]:
    """Load Oracle-Symbolic evaluation outcomes (secondary)."""
    outcomes_path = DATA_PROCESSED_DIR / "oracle_evaluation_outcomes.json"
    data = load_json_file(outcomes_path)
    return data.get('outcomes', []) if data else []

def build_evaluation_summary(
    symbolic_outcomes: List[Dict[str, Any]],
    baseline_outcomes: List[Dict[str, Any]],
    oracle_outcomes: List[Dict[str, Any]],
    stats_results: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Construct the final evaluation summary dictionary."""
    
    # Symbolic Metrics
    sym_success_rate = calculate_success_rate(symbolic_outcomes)
    sym_step_eff = calculate_step_efficiency(symbolic_outcomes)
    sym_fail_dist = aggregate_failure_distribution(symbolic_outcomes)
    sym_total = len(symbolic_outcomes)
    sym_successes = sum(1 for o in symbolic_outcomes if o.get('success', False))
    sym_failures = sym_total - sym_successes

    # Baseline Metrics
    base_success_rate = calculate_success_rate(baseline_outcomes)
    base_step_eff = calculate_step_efficiency(baseline_outcomes)
    base_fail_dist = aggregate_failure_distribution(baseline_outcomes)
    base_total = len(baseline_outcomes)
    base_successes = sum(1 for o in baseline_outcomes if o.get('success', False))
    base_failures = base_total - base_successes

    # Oracle Metrics (Secondary)
    orc_success_rate = calculate_success_rate(oracle_outcomes)
    orc_step_eff = calculate_step_efficiency(oracle_outcomes)
    orc_fail_dist = aggregate_failure_distribution(oracle_outcomes)
    orc_total = len(oracle_outcomes)
    orc_successes = sum(1 for o in oracle_outcomes if o.get('success', False))

    # Statistical Significance
    p_value = None
    is_significant = False
    if stats_results:
        p_value = stats_results.get('p_value')
        is_significant = p_value is not None and p_value < 0.05

    summary = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_tasks_symbolic": sym_total,
        "total_tasks_baseline": base_total,
        "total_tasks_oracle": orc_total,
        "symbolic": {
            "success_rate": round(sym_success_rate, 4),
            "success_count": sym_successes,
            "failure_count": sym_failures,
            "step_efficiency": round(sym_step_eff, 2),
            "failure_distribution": sym_fail_dist
        },
        "baseline_visual": {
            "success_rate": round(base_success_rate, 4),
            "success_count": base_successes,
            "failure_count": base_failures,
            "step_efficiency": round(base_step_eff, 2),
            "failure_distribution": base_fail_dist
        },
        "oracle_symbolic": {
            "success_rate": round(orc_success_rate, 4),
            "success_count": orc_successes,
            "failure_count": orc_total - orc_successes,
            "step_efficiency": round(orc_step_eff, 2),
            "failure_distribution": orc_fail_dist
        },
        "statistical_test": {
            "method": "Permutation Test (Symbolic vs Baseline Visual)",
            "p_value": p_value,
            "is_significant": is_significant,
            "null_hypothesis": "No difference in success rates between Symbolic-Guava and Baseline-Guava (Visual)",
            "iterations": stats_results.get('iterations') if stats_results else None
        },
        "comparison_summary": {
            "symbolic_vs_baseline_diff": round(sym_success_rate - base_success_rate, 4),
            "symbolic_vs_oracle_diff": round(sym_success_rate - orc_success_rate, 4),
            "primary_conclusion": "Significant" if is_significant else "Not Significant"
        }
    }
    
    return summary

def write_evaluation_results(summary: Dict[str, Any], output_path: Path) -> None:
    """Write the evaluation summary to the output JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    print(f"Evaluation results written to: {output_path}")

def main() -> None:
    """Main entry point for T037."""
    print("Starting T037: Evaluation Results Generation...")
    
    # Load data from previous tasks
    symbolic_outcomes = load_symbolic_outcomes()
    baseline_outcomes = load_baseline_outcomes()
    oracle_outcomes = load_oracle_outcomes()
    stats_results = load_stats_test_results()
    
    if not symbolic_outcomes and not baseline_outcomes:
        print("WARNING: No evaluation outcomes found for Symbolic or Baseline agents.")
        print("Generating empty results structure.")
    
    # Build summary
    summary = build_evaluation_summary(
        symbolic_outcomes,
        baseline_outcomes,
        oracle_outcomes,
        stats_results
    )
    
    # Write output
    output_path = DATA_ARTIFACTS_DIR / "evaluation_results.json"
    write_evaluation_results(summary, output_path)
    
    print("T037 completed successfully.")

if __name__ == "__main__":
    main()