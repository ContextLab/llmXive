import os
import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from scipy import stats

# Local imports matching API surface
from config import load_config, get_config_paths
from analysis.metrics import load_metrics_from_csv, calculate_aucc
from analysis.stats import paired_ttest_aucc, summarize_aucc_distribution, check_catastrophic_forgetting
from utils.logging import get_logger

logger = get_logger(__name__)

def load_aggregated_results(baseline_dir: str, cap_dir: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Load metrics from multiple runs for both baseline and CAP simulations.
    Expects CSV files in the specified directories.
    """
    baseline_files = list(Path(baseline_dir).glob("*.csv"))
    cap_files = list(Path(cap_dir).glob("*.csv"))

    if not baseline_files:
        logger.warning(f"No baseline result files found in {baseline_dir}")
    if not cap_files:
        logger.warning(f"No CAP result files found in {cap_dir}")

    def load_all_from_dir(files: List[Path]) -> List[Dict]:
        results = []
        for f in files:
            try:
                data = load_metrics_from_csv(str(f))
                # Ensure we have the necessary fields
                if isinstance(data, list):
                    results.extend(data)
                else:
                    results.append(data)
            except Exception as e:
                logger.error(f"Failed to load {f}: {e}")
        return results

    return load_all_from_dir(baseline_files), load_all_from_dir(cap_files)

def extract_aucc_values(results: List[Dict]) -> np.ndarray:
    """Extract AUCC values from a list of result dictionaries."""
    aucc_values = []
    for r in results:
        if 'aucc' in r:
            aucc_values.append(float(r['aucc']))
        elif 'accuracy' in r and 'cycles' in r:
            # Fallback: calculate AUCC if not explicitly stored
            # Assuming accuracy is a list or can be derived
            # For simplicity in this report generator, we expect pre-calculated AUCC
            logger.warning("AUCC not found in result, skipping calculation fallback in report")
        else:
            logger.warning(f"Could not extract AUCC from result: {r}")
    return np.array(aucc_values)

def extract_final_accuracy(results: List[Dict]) -> np.ndarray:
    """Extract final accuracy values."""
    acc_values = []
    for r in results:
        if 'final_accuracy' in r:
            acc_values.append(float(r['final_accuracy']))
        elif 'accuracy' in r:
            # Assume the last value if it's a list, or the value itself
            acc = r['accuracy']
            if isinstance(acc, list):
                acc_values.append(float(acc[-1]))
            else:
                acc_values.append(float(acc))
    return np.array(acc_values)

def extract_avg_prompt_length(results: List[Dict]) -> np.ndarray:
    """Extract average mid-training prompt length (specifically for CAP)."""
    lengths = []
    for r in results:
        if 'avg_prompt_length' in r:
            lengths.append(float(r['avg_prompt_length']))
        elif 'prompt_length' in r:
            # If it's a list of lengths per cycle, average the middle 50%
            lengths_list = r['prompt_length']
            if isinstance(lengths_list, list):
                mid_start = len(lengths_list) // 4
                mid_end = 3 * len(lengths_list) // 4
                lengths.append(float(np.mean(lengths_list[mid_start:mid_end])))
            else:
                lengths.append(float(lengths_list))
    return np.array(lengths)

def generate_comparison_report(
    baseline_results: List[Dict],
    cap_results: List[Dict],
    output_path: str
) -> Dict[str, Any]:
    """
    Generate a comparative statistical report between Baseline and CAP-ZPPO.
    Returns a dictionary of report metrics and generates plots.
    """
    logger.info("Generating comparative report...")

    # 1. Extract Data
    baseline_aucc = extract_aucc_values(baseline_results)
    cap_aucc = extract_aucc_values(cap_results)

    baseline_acc = extract_final_accuracy(baseline_results)
    cap_acc = extract_final_accuracy(cap_results)

    cap_prompt_len = extract_avg_prompt_length(cap_results)

    report_data = {
        "n_baseline": len(baseline_results),
        "n_cap": len(cap_results),
        "baseline_aucc_mean": float(np.mean(baseline_aucc)) if len(baseline_aucc) else 0.0,
        "baseline_aucc_std": float(np.std(baseline_aucc)) if len(baseline_aucc) else 0.0,
        "cap_aucc_mean": float(np.mean(cap_aucc)) if len(cap_aucc) else 0.0,
        "cap_aucc_std": float(np.std(cap_aucc)) if len(cap_aucc) else 0.0,
        "aucc_difference": float(np.mean(cap_aucc) - np.mean(baseline_aucc)) if len(cap_aucc) and len(baseline_aucc) else 0.0,
    }

    # 2. Statistical Tests
    # Paired t-test on AUCC (assuming runs are paired by seed)
    # If lengths differ, we take the minimum length for pairing
    min_len = min(len(baseline_aucc), len(cap_aucc))
    if min_len >= 2:
        paired_baseline = baseline_aucc[:min_len]
        paired_cap = cap_aucc[:min_len]
        t_stat, p_val = paired_ttest_aucc(paired_baseline, paired_cap)
        report_data["t_statistic"] = float(t_stat)
        report_data["p_value"] = float(p_val)
        report_data["statistically_significant"] = p_val < 0.05
    else:
        report_data["t_statistic"] = None
        report_data["p_value"] = None
        report_data["statistically_significant"] = False
        logger.warning("Insufficient data for paired t-test (need >= 2 pairs)")

    # 3. Catastrophic Forgetting Check
    if len(baseline_acc) and len(cap_acc):
        # Check if CAP final accuracy is significantly lower than Baseline
        # We want to ensure it's not *worse*
        forgetting_check = check_catastrophic_forgetting(baseline_acc, cap_acc)
        report_data["catastrophic_forgetting_detected"] = forgetting_check.get("detected", False)
        report_data["accuracy_drop_mean"] = float(forgetting_check.get("mean_drop", 0.0))
    else:
        report_data["catastrophic_forgetting_detected"] = False
        report_data["accuracy_drop_mean"] = 0.0

    # 4. Prompt Length Analysis
    if len(cap_prompt_len) > 0:
        report_data["cap_avg_prompt_length_mid_training"] = float(np.mean(cap_prompt_len))
        report_data["cap_prompt_length_std"] = float(np.std(cap_prompt_len))
    else:
        report_data["cap_avg_prompt_length_mid_training"] = 0.0
        report_data["cap_prompt_length_std"] = 0.0

    # 5. Generate Plots
    plots_dir = Path(output_path).parent / "figures"
    plots_dir.mkdir(parents=True, exist_ok=True)

    # Plot 1: AUCC Distribution
    plt.figure(figsize=(10, 6))
    if len(baseline_aucc) > 0:
        sns.kdeplot(baseline_aucc, label="Baseline AUCC", fill=True, alpha=0.5)
    if len(cap_aucc) > 0:
        sns.kdeplot(cap_aucc, label="CAP-ZPPO AUCC", fill=True, alpha=0.5)
    plt.title("Distribution of AUCC (Area Under Convergence Curve)")
    plt.xlabel("AUCC Score")
    plt.ylabel("Density")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(plots_dir / "aucc_distribution.png", dpi=150)
    plt.close()

    # Plot 2: Convergence Curves (if cycle data is available in results)
    # We attempt to plot if 'accuracy_per_cycle' or similar is present
    # Since load_metrics_from_csv might return a flat row, we check for list data
    # For this report, we plot a representative curve if possible
    representative_baseline = None
    representative_cap = None

    if baseline_results:
        for r in baseline_results:
            if 'accuracy_per_cycle' in r and isinstance(r['accuracy_per_cycle'], list):
                representative_baseline = r['accuracy_per_cycle']
                break
            # Fallback if stored as string or different format
            if 'accuracy' in r and isinstance(r['accuracy'], list):
                representative_baseline = r['accuracy']
                break

    if cap_results:
        for r in cap_results:
            if 'accuracy_per_cycle' in r and isinstance(r['accuracy_per_cycle'], list):
                representative_cap = r['accuracy_per_cycle']
                break
            if 'accuracy' in r and isinstance(r['accuracy'], list):
                representative_cap = r['accuracy']
                break

    if representative_baseline or representative_cap:
        plt.figure(figsize=(10, 6))
        if representative_baseline:
            plt.plot(representative_baseline, label="Baseline Convergence", marker='o')
        if representative_cap:
            plt.plot(representative_cap, label="CAP-ZPPO Convergence", marker='x')
        plt.title("Representative Convergence Curves")
        plt.xlabel("Training Cycle")
        plt.ylabel("Accuracy")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig(plots_dir / "convergence_curves.png", dpi=150)
        plt.close()
    else:
        logger.warning("Could not find per-cycle accuracy data for convergence plot.")

    # Plot 3: Prompt Length Histogram (CAP only)
    if len(cap_prompt_len) > 0:
        plt.figure(figsize=(10, 6))
        sns.histplot(cap_prompt_len, bins=10, kde=True, color='purple')
        plt.title("Distribution of Mid-Training Prompt Lengths (CAP)")
        plt.xlabel("Prompt Length (tokens)")
        plt.ylabel("Frequency")
        plt.savefig(plots_dir / "prompt_length_distribution.png", dpi=150)
        plt.close()

    # 6. Save Report
    with open(output_path, 'w') as f:
        json.dump(report_data, f, indent=2)

    logger.info(f"Report saved to {output_path}")
    return report_data

def main():
    """
    Entry point to generate the comparative report.
    Reads results from data/metrics/baseline and data/metrics/cap,
    generates plots in data/figures, and saves the report to data/metrics/comparison_report.json.
    """
    config = load_config()
    paths = get_config_paths(config)

    baseline_dir = paths.get('baseline_results_dir', 'data/metrics/baseline')
    cap_dir = paths.get('cap_results_dir', 'data/metrics/cap')
    output_file = paths.get('comparison_report_path', 'data/metrics/comparison_report.json')

    logger.info(f"Loading baseline results from: {baseline_dir}")
    logger.info(f"Loading CAP results from: {cap_dir}")

    baseline_results, cap_results = load_aggregated_results(baseline_dir, cap_dir)

    if not baseline_results and not cap_results:
        logger.error("No results found to compare. Ensure simulations have been run.")
        return

    report = generate_comparison_report(baseline_results, cap_results, output_file)

    print("\n--- Comparative Analysis Summary ---")
    print(f"Baseline Runs: {report['n_baseline']}")
    print(f"CAP Runs: {report['n_cap']}")
    print(f"AUCC Difference (CAP - Baseline): {report['aucc_difference']:.4f}")
    print(f"Mean Baseline AUCC: {report['baseline_aucc_mean']:.4f} (±{report['baseline_aucc_std']:.4f})")
    print(f"Mean CAP AUCC: {report['cap_aucc_mean']:.4f} (±{report['cap_aucc_std']:.4f})")
    print(f"Statistically Significant (p < 0.05): {report['statistically_significant']}")
    if report['p_value'] is not None:
        print(f"P-Value: {report['p_value']:.4f}")
    print(f"Catastrophic Forgetting Detected: {report['catastrophic_forgetting_detected']}")
    print(f"CAP Avg Prompt Length (Mid-Training): {report['cap_avg_prompt_length_mid_training']:.2f}")
    print(f"Report saved to: {output_file}")

if __name__ == "__main__":
    main()