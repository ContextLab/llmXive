"""
Script to aggregate baseline and quantum metrics and generate a statistical report.

This script performs the following:
1. Loads `data/results/baseline_metrics.json` and `data/results/quantum_metrics.json`.
2. Extracts accuracy and F1 scores for each seed.
3. Calls `analysis.stats_test.run_stats_analysis` to compute paired t-tests,
   Cohen's d, and bootstrap confidence intervals.
4. Outputs the comprehensive report to `data/results/stats_report.json`.

All results are framed as "associational improvements" to satisfy FR-006.
"""
import os
import sys
import json
import argparse
from typing import Dict, Any, List, Tuple

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from analysis.stats_test import run_stats_analysis
from utils.config import set_environment

def load_metrics_from_json(file_path: str) -> List[Dict[str, Any]]:
    """
    Load metrics from a JSON file containing a list of results per seed.
    Expects a structure like: [{"seed": 1, "accuracy": 0.65, "f1": 0.64}, ...]
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Required metrics file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        # If it's a single dict, wrap it, but expect list per task design
        if isinstance(data, dict):
            return [data]
        raise ValueError(f"Expected list of metrics in {file_path}, got {type(data)}")

    return data

def aggregate_seed_results(
    baseline_data: List[Dict[str, Any]],
    quantum_data: List[Dict[str, Any]]
) -> Tuple[List[float], List[float], List[float], List[float]]:
    """
    Align baseline and quantum results by seed and extract metric lists.
    Returns: (baseline_accs, quantum_accs, baseline_f1s, quantum_f1s)
    """
    # Create lookup by seed
    baseline_map = {item['seed']: item for item in baseline_data}
    quantum_map = {item['seed']: item for item in quantum_data}

    common_seeds = sorted(set(baseline_map.keys()) & set(quantum_map.keys()))

    if not common_seeds:
        raise ValueError("No common seeds found between baseline and quantum results.")

    baseline_accs = []
    quantum_accs = []
    baseline_f1s = []
    quantum_f1s = []

    for seed in common_seeds:
        b_item = baseline_map[seed]
        q_item = quantum_map[seed]

        # Extract metrics
        b_acc = b_item.get('accuracy')
        q_acc = q_item.get('accuracy')
        b_f1 = b_item.get('f1')
        q_f1 = q_item.get('f1')

        if any(v is None for v in [b_acc, q_acc, b_f1, q_f1]):
            raise ValueError(f"Missing metric values for seed {seed}")

        baseline_accs.append(b_acc)
        quantum_accs.append(q_acc)
        baseline_f1s.append(b_f1)
        quantum_f1s.append(q_f1)

    return baseline_accs, quantum_accs, baseline_f1s, quantum_f1s

def main():
    parser = argparse.ArgumentParser(description="Generate statistical report comparing baseline and quantum models.")
    parser.add_argument('--baseline-path', type=str, default='data/results/baseline_metrics.json',
                        help='Path to baseline metrics JSON')
    parser.add_argument('--quantum-path', type=str, default='data/results/quantum_metrics.json',
                        help='Path to quantum metrics JSON')
    parser.add_argument('--output-path', type=str, default='data/results/stats_report.json',
                        help='Path for output statistical report')
    args = parser.parse_args()

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Loading baseline metrics from: {args.baseline_path}")
    baseline_data = load_metrics_from_json(args.baseline_path)

    print(f"Loading quantum metrics from: {args.quantum_path}")
    quantum_data = load_metrics_from_json(args.quantum_path)

    print("Aligning metrics by seed...")
    try:
        b_accs, q_accs, b_f1s, q_f1s = aggregate_seed_results(baseline_data, quantum_data)
    except Exception as e:
        print(f"Error aligning metrics: {e}")
        sys.exit(1)

    print(f"Found {len(b_accs)} paired seeds.")

    # Run statistical analysis
    # We run analysis on Accuracy first, then F1
    print("Running statistical analysis on Accuracy...")
    stats_acc = run_stats_analysis(b_accs, q_accs, metric_name="Accuracy")

    print("Running statistical analysis on F1...")
    stats_f1 = run_stats_analysis(b_f1s, q_f1s, metric_name="F1")

    # Construct the final report
    report = {
        "description": "Statistical comparison of Quantum Adapter vs. Frozen BERT Baseline on WiC.",
        "fr_006_framing": "All results describe associational improvements in model performance. No causal claims are made regarding the mechanism of ambiguity resolution.",
        "methodology": {
            "test": "Paired t-test (alpha=0.05) with Bootstrap Confidence Intervals (k=1000)",
            "seeds_used": len(b_accs),
            "metrics_analyzed": ["Accuracy", "F1"]
        },
        "results": {
            "accuracy": stats_acc,
            "f1": stats_f1
        }
    }

    # Write report
    print(f"Writing report to: {args.output_path}")
    with open(args.output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print("Stats report generation complete.")

if __name__ == "__main__":
    main()