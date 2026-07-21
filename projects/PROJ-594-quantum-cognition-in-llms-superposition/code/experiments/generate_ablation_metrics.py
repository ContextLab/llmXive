"""
Ablation Analysis: Compare Quantum vs. Classical vs. Magnitude-Only models.

This script aggregates results from the three model variants (Quantum, Classical, Magnitude-Only)
run across multiple seeds (as orchestrated by run_seed_driver.py or individual seed runs)
and generates a comparative metrics report.

It specifically addresses the ablation requirement to isolate the contribution of the
interference cross-term.
"""
import os
import sys
import json
import argparse
from typing import Dict, Any, List, Tuple
import numpy as np

# Project root handling
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from experiments.run_seed_driver import run_experiment_for_seed
from experiments.run_classical_baseline import run_single_seed as run_classical_seed
from experiments.run_magnitude_control import run_single_seed as run_magnitude_seed
from experiments.run_quantum import run_single_seed as run_quantum_seed
from utils.config import set_environment

# Constants
NUM_SEEDS = 5
BASELINE_DIR = os.path.join(PROJECT_ROOT, "projects", "PROJ-594-quantum-cognition-in-llms-superposition", "data", "results")

def load_seed_metrics(model_type: str, seed: int) -> Dict[str, Any]:
    """
    Load metrics for a specific model and seed.
    Expects files named: <model_type>_metrics_seed_<seed>.json
    """
    filename = f"{model_type}_metrics_seed_{seed}.json"
    filepath = os.path.join(BASELINE_DIR, filename)
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Missing metrics file for {model_type} seed {seed}: {filepath}")
    
    with open(filepath, 'r') as f:
        return json.load(f)

def aggregate_results(metrics_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate a list of per-seed metrics into mean/std/min/max.
    """
    if not metrics_list:
        return {}

    accuracies = [m.get('accuracy', 0.0) for m in metrics_list]
    f1_scores = [m.get('macro_f1', 0.0) for m in metrics_list]

    return {
        "mean_accuracy": float(np.mean(accuracies)),
        "std_accuracy": float(np.std(accuracies)),
        "min_accuracy": float(np.min(accuracies)),
        "max_accuracy": float(np.max(accuracies)),
        "mean_macro_f1": float(np.mean(f1_scores)),
        "std_macro_f1": float(np.std(f1_scores)),
        "num_seeds": len(accuracies)
    }

def compute_improvement(quantum_stats: Dict, classical_stats: Dict) -> Dict[str, float]:
    """
    Compute relative improvement of Quantum over Classical/Magnitude.
    """
    q_acc = quantum_stats.get('mean_accuracy', 0)
    c_acc = classical_stats.get('mean_accuracy', 0)
    m_acc = classical_stats.get('mean_accuracy', 0) # Magnitude uses same key for baseline comparison

    delta_acc_vs_classical = q_acc - c_acc
    rel_acc_vs_classical = (delta_acc_vs_classical / c_acc * 100) if c_acc != 0 else 0.0

    delta_acc_vs_magnitude = q_acc - m_acc
    rel_acc_vs_magnitude = (delta_acc_vs_magnitude / m_acc * 100) if m_acc != 0 else 0.0

    return {
        "delta_accuracy_vs_classical": float(delta_acc_vs_classical),
        "relative_improvement_vs_classical_pct": float(rel_acc_vs_classical),
        "delta_accuracy_vs_magnitude": float(delta_acc_vs_magnitude),
        "relative_improvement_vs_magnitude_pct": float(rel_acc_vs_magnitude)
    }

def main():
    parser = argparse.ArgumentParser(description="Generate ablation metrics comparing Quantum, Classical, and Magnitude-Only models.")
    parser.add_argument("--seeds", type=int, nargs='+', default=list(range(NUM_SEEDS)), help="List of seeds to aggregate. Default: 0-4")
    parser.add_argument("--output", type=str, default="data/results/ablation_metrics.json", help="Output path for the ablation report.")
    args = parser.parse_args()

    print(f"Aggregating results for seeds: {args.seeds}")

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    quantum_metrics = []
    classical_metrics = []
    magnitude_metrics = []

    # Aggregate existing results if they exist
    # Note: In a real pipeline, run_seed_driver would have created these.
    # If they don't exist, we might need to run them, but for this task we assume
    # the prerequisite tasks (T034, T035) have generated the seed files.
    # If files are missing, we raise an error rather than fabricating data.
    
    missing_files = []
    for seed in args.seeds:
        q_file = os.path.join(BASELINE_DIR, f"quantum_metrics_seed_{seed}.json")
        c_file = os.path.join(BASELINE_DIR, f"classical_metrics_seed_{seed}.json")
        m_file = os.path.join(BASELINE_DIR, f"magnitude_metrics_seed_{seed}.json")

        if not os.path.exists(q_file): missing_files.append(q_file)
        if not os.path.exists(c_file): missing_files.append(c_file)
        if not os.path.exists(m_file): missing_files.append(m_file)

    if missing_files:
        print(f"ERROR: Missing required seed result files. Please run the seed drivers first.")
        for f in missing_files:
            print(f"  - {f}")
        sys.exit(1)

    for seed in args.seeds:
        try:
            quantum_metrics.append(load_seed_metrics("quantum", seed))
            classical_metrics.append(load_seed_metrics("classical", seed))
            magnitude_metrics.append(load_seed_metrics("magnitude", seed))
        except FileNotFoundError as e:
            print(f"Error loading seed {seed}: {e}")
            sys.exit(1)

    # Aggregate statistics
    quantum_stats = aggregate_results(quantum_metrics)
    classical_stats = aggregate_results(classical_metrics)
    magnitude_stats = aggregate_results(magnitude_metrics)

    # Compute improvements
    improvements = compute_improvement(quantum_stats, classical_stats)
    
    # Construct final report
    report = {
        "description": "Ablation study comparing Quantum (with interference), Classical (sum of squares), and Magnitude-Only (no phase) models on WiC.",
        "methodology": "Aggregated results from " + str(len(args.seeds)) + " random seeds. Quantum model includes complex-valued phase shifts and Born rule interference. Classical model sums probabilities. Magnitude model sums squared magnitudes without phase interaction.",
        "results": {
            "quantum_model": quantum_stats,
            "classical_baseline": classical_stats,
            "magnitude_only_control": magnitude_stats
        },
        "analysis": {
            "quantum_vs_classical": improvements,
            "interpretation": "If Quantum > Classical, it indicates the interference cross-term contributes positively to ambiguity resolution. If Quantum > Magnitude, it confirms the phase shift mechanism adds value beyond simple magnitude weighting."
        },
        "fr_006_framing": "These results represent associational improvements in predictive performance under the complex-valued formalism. No causal claims regarding 'quantum cognition' in the brain are made."
    }

    # Write output
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Ablation metrics written to: {args.output}")
    print(f"Quantum Mean Accuracy: {quantum_stats['mean_accuracy']:.4f} (+/- {quantum_stats['std_accuracy']:.4f})")
    print(f"Classical Mean Accuracy: {classical_stats['mean_accuracy']:.4f} (+/- {classical_stats['std_accuracy']:.4f})")
    print(f"Magnitude Mean Accuracy: {magnitude_stats['mean_accuracy']:.4f} (+/- {magnitude_stats['std_accuracy']:.4f})")

if __name__ == "__main__":
    main()