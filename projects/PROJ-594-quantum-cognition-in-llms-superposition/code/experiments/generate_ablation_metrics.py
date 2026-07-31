import os
import sys
import json
import argparse
from typing import Dict, Any, List, Tuple
import numpy as np

# Ensure project root is in path for imports
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from utils.config import get_config
from utils.logging import detect_nan_inf

def load_seed_metrics(model_type: str, num_seeds: int = 5) -> List[Dict[str, Any]]:
    """
    Load metrics from the aggregated seed results for a specific model type.
    Expects files like: data/results/baseline_metrics.json, data/results/quantum_metrics.json,
    data/results/classical_baseline_metrics.json, data/results/magnitude_control_metrics.json
    """
    if model_type == "baseline":
        file_path = "data/results/baseline_metrics.json"
    elif model_type == "quantum":
        file_path = "data/results/quantum_metrics.json"
    elif model_type == "classical":
        file_path = "data/results/classical_baseline_metrics.json"
    elif model_type == "magnitude":
        file_path = "data/results/magnitude_control_metrics.json"
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Required metrics file not found: {file_path}. "
                                f"Run the corresponding experiment script first.")

    with open(file_path, 'r') as f:
        data = json.load(f)

    # The file is expected to contain a list of seed results or a single aggregated object
    # Based on run_seed_driver and run_stats patterns, we expect a list of dicts or a dict with 'seeds'
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        if 'seeds' in data:
            return data['seeds']
        else:
            # Treat the whole dict as a single seed result for simplicity if structure varies
            return [data]
    else:
        raise ValueError(f"Unexpected data structure in {file_path}")

def aggregate_results(seed_metrics: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Aggregate metrics (accuracy, f1) across seeds to compute mean and std.
    """
    if not seed_metrics:
        return {"accuracy_mean": 0.0, "accuracy_std": 0.0, "f1_mean": 0.0, "f1_std": 0.0}

    accuracies = [m.get("accuracy", 0.0) for m in seed_metrics]
    f1s = [m.get("macro_f1", 0.0) for m in seed_metrics]

    # Check for NaN/Inf before aggregating
    if detect_nan_inf(accuracies) or detect_nan_inf(f1s):
        raise RuntimeError("NaN or Inf detected in metrics during aggregation.")

    return {
        "accuracy_mean": float(np.mean(accuracies)),
        "accuracy_std": float(np.std(accuracies)),
        "f1_mean": float(np.mean(f1s)),
        "f1_std": float(np.std(f1s)),
        "num_seeds": len(seed_metrics)
    }

def compute_improvement(base_metrics: Dict[str, float], target_metrics: Dict[str, float]) -> Dict[str, float]:
    """
    Compute the absolute and relative improvement of target over baseline.
    """
    acc_diff = target_metrics["accuracy_mean"] - base_metrics["accuracy_mean"]
    f1_diff = target_metrics["f1_mean"] - base_metrics["f1_mean"]

    # Relative improvement (handle division by zero)
    acc_rel = (acc_diff / base_metrics["accuracy_mean"]) * 100.0 if base_metrics["accuracy_mean"] != 0 else 0.0
    f1_rel = (f1_diff / base_metrics["f1_mean"]) * 100.0 if base_metrics["f1_mean"] != 0 else 0.0

    return {
        "accuracy_diff": acc_diff,
        "accuracy_rel_percent": acc_rel,
        "f1_diff": f1_diff,
        "f1_rel_percent": f1_rel
    }

def main():
    parser = argparse.ArgumentParser(description="Generate ablation metrics comparing Quantum, Classical, and Magnitude-Only models.")
    parser.add_argument("--num-seeds", type=int, default=5, help="Number of seeds used in experiments")
    args = parser.parse_args()

    print("Loading baseline metrics...")
    try:
        baseline_seeds = load_seed_metrics("baseline", args.num_seeds)
        baseline_agg = aggregate_results(baseline_seeds)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure 'data/results/baseline_metrics.json' exists by running code/experiments/run_seed_driver.py or run_baseline.py first.")
        sys.exit(1)

    print("Loading Quantum metrics...")
    try:
        quantum_seeds = load_seed_metrics("quantum", args.num_seeds)
        quantum_agg = aggregate_results(quantum_seeds)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure 'data/results/quantum_metrics.json' exists by running code/experiments/run_quantum.py first.")
        sys.exit(1)

    print("Loading Classical Baseline metrics...")
    try:
        classical_seeds = load_seed_metrics("classical", args.num_seeds)
        classical_agg = aggregate_results(classical_seeds)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure 'data/results/classical_baseline_metrics.json' exists by running code/experiments/run_classical_baseline.py first.")
        sys.exit(1)

    print("Loading Magnitude-Only Control metrics...")
    try:
        magnitude_seeds = load_seed_metrics("magnitude", args.num_seeds)
        magnitude_agg = aggregate_results(magnitude_seeds)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure 'data/results/magnitude_control_metrics.json' exists by running code/experiments/run_magnitude_control.py first.")
        sys.exit(1)

    # Compute improvements relative to the frozen BERT baseline
    quantum_vs_baseline = compute_improvement(baseline_agg, quantum_agg)
    classical_vs_baseline = compute_improvement(baseline_agg, classical_agg)
    magnitude_vs_baseline = compute_improvement(baseline_agg, magnitude_agg)

    # Compute improvements relative to Classical (to isolate interference)
    quantum_vs_classical = compute_improvement(classical_agg, quantum_agg)
    magnitude_vs_classical = compute_improvement(classical_agg, magnitude_agg)

    ablation_report = {
        "description": "Ablation study comparing Quantum (with interference), Classical (sum of squares), and Magnitude-Only (no phase) models against Frozen BERT baseline.",
        "models": {
            "baseline": baseline_agg,
            "quantum": quantum_agg,
            "classical": classical_agg,
            "magnitude": magnitude_agg
        },
        "comparisons": {
            "quantum_vs_baseline": quantum_vs_baseline,
            "classical_vs_baseline": classical_vs_baseline,
            "magnitude_vs_baseline": magnitude_vs_baseline,
            "quantum_vs_classical": quantum_vs_classical,
            "magnitude_vs_classical": magnitude_vs_classical
        },
        "conclusion": {
            "interference_contribution": quantum_vs_classical["accuracy_diff"],
            "phase_contribution": (quantum_vs_classical["accuracy_diff"] - magnitude_vs_classical["accuracy_diff"])
        }
    }

    output_path = "data/results/ablation_metrics.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(ablation_report, f, indent=2)

    print(f"Ablation metrics successfully written to {output_path}")
    print(f"Quantum Accuracy: {quantum_agg['accuracy_mean']:.4f} (+/- {quantum_agg['accuracy_std']:.4f})")
    print(f"Classical Accuracy: {classical_agg['accuracy_mean']:.4f} (+/- {classical_agg['accuracy_std']:.4f})")
    print(f"Magnitude Accuracy: {magnitude_agg['accuracy_mean']:.4f} (+/- {magnitude_agg['accuracy_std']:.4f})")
    print(f"Baseline Accuracy: {baseline_agg['accuracy_mean']:.4f} (+/- {baseline_agg['accuracy_std']:.4f})")

if __name__ == "__main__":
    main()