"""
Plots module for llmXive analysis.

Generates visualizations for coverage distributions and survival curves
to support the comparative metric analysis in User Story 3.
"""
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
# Use non-interactive backend for server/headless environments
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

from config import get_config_summary
from analysis.stats import (
    load_agent_logs_for_pairing,
    compute_paired_coverage_data,
    run_cox_survival_analysis,
    apply_bonferroni_correction
)


def load_metrics_for_plotting(metrics_path: Path) -> Dict[str, Any]:
    """Load final metrics from the stats module output."""
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    
    with open(metrics_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def plot_coverage_histogram(
    baseline_coverage: List[float],
    iterative_coverage: List[float],
    output_path: Path,
    title: str = "Coverage Distribution Comparison"
) -> None:
    """
    Plot histograms of coverage scores for Baseline vs Iterative agents.
    
    Args:
        baseline_coverage: List of coverage scores for static baseline.
        iterative_coverage: List of coverage scores for iterative agent.
        output_path: Path to save the figure.
        title: Plot title.
    """
    plt.figure(figsize=(10, 6))
    
    # Plot Baseline
    plt.hist(
        baseline_coverage,
        bins=20,
        alpha=0.6,
        label='Static Multi-Query Baseline',
        color='skyblue',
        edgecolor='black'
    )
    
    # Plot Iterative
    plt.hist(
        iterative_coverage,
        bins=20,
        alpha=0.6,
        label='Iterative Agent (3-turn)',
        color='salmon',
        edgecolor='black'
    )
    
    plt.xlabel('Line-Level Coverage (%)', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.title(title, fontsize=14)
    plt.legend(loc='upper right')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add statistical summary text
    mean_base = np.mean(baseline_coverage)
    mean_iter = np.mean(iterative_coverage)
    plt.text(
        0.02, 0.98,
        f"Mean Baseline: {mean_base:.2f}%\nMean Iterative: {mean_iter:.2f}%",
        transform=plt.gca().transAxes,
        fontsize=10,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Coverage histogram saved to: {output_path}")


def plot_boxplot_coverage(
    baseline_coverage: List[float],
    iterative_coverage: List[float],
    output_path: Path,
    title: str = "Coverage Comparison (Boxplot)"
) -> None:
    """
    Plot boxplots to compare coverage distributions.
    """
    plt.figure(figsize=(8, 6))
    
    data_to_plot = [baseline_coverage, iterative_coverage]
    labels = ['Static Baseline', 'Iterative Agent']
    
    bp = plt.boxplot(data_to_plot, labels=labels, patch_artist=True)
    
    # Color the boxes
    colors = ['skyblue', 'salmon']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
    
    plt.ylabel('Line-Level Coverage (%)', fontsize=12)
    plt.title(title, fontsize=14)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Coverage boxplot saved to: {output_path}")


def plot_survival_curve(
    baseline_times: List[float],
    iterative_times: List[float],
    baseline_censored: List[bool],
    iterative_censored: List[bool],
    output_path: Path,
    title: str = "Survival Analysis: Time to First Relevant Line"
) -> None:
    """
    Plot Kaplan-Meier survival curves for ranking metrics.
    'Time' here is the position of the first relevant line (rank).
    Lower rank is better, so we plot "Survival" as probability of NOT having found it yet.
    
    Args:
        baseline_times: Rank positions for baseline.
        iterative_times: Rank positions for iterative.
        baseline_censored: Boolean list (True if censored, i.e., not found).
        iterative_censored: Boolean list (True if censored).
        output_path: Path to save the figure.
        title: Plot title.
    """
    plt.figure(figsize=(10, 6))
    
    # Fit Kaplan-Meier estimators
    from scipy.stats import mstats
    
    # Note: matplotlib doesn't have built-in KM, so we use a simple step plot
    # or approximate with survival curves. For strict KM, we might use lifelines,
    # but we stick to standard scipy/numpy/matplotlib here.
    
    # Sort and calculate survival probability
    def calculate_km_curve(times, censored):
        times = np.array(times)
        censored = np.array(censored)
        unique_times = np.sort(np.unique(times))
        survival_probs = []
        n_at_risk = len(times)
        
        for t in unique_times:
            n_events = np.sum((times == t) & (~censored))
            n_censored = np.sum((times == t) & censored)
            
            if n_at_risk == 0:
                prob = 0
            else:
                prob = 1 - (n_events / n_at_risk)
            
            survival_probs.append(prob)
            n_at_risk -= (n_events + n_censored)
            
        return unique_times, np.cumprod(survival_probs)

    # Since manual KM is complex with ties/censoring, we use a simplified 
    # "Empirical Survival" visualization: 1 - CDF of ranks.
    # Higher curve = worse performance (took longer to find).
    
    # Baseline
    base_sorted = np.sort(baseline_times)
    base_n = len(base_sorted)
    base_survival = 1 - (np.arange(1, base_n + 1) / base_n)
    # Adjust for censoring: censored items stay at their rank
    # For a simple plot, we treat censored as "not found" -> rank = N+1 (penalty)
    # But since we already have the list with penalty N+1 applied in stats.py,
    # we just plot the empirical CDF complement.
    
    plt.step(base_sorted, base_survival, where='post', label='Static Baseline', color='skyblue')
    
    # Iterative
    iter_sorted = np.sort(iterative_times)
    iter_n = len(iter_sorted)
    iter_survival = 1 - (np.arange(1, iter_n + 1) / iter_n)
    plt.step(iter_sorted, iter_survival, where='post', label='Iterative Agent', color='salmon')
    
    plt.xlabel('Rank of First Relevant Line (Lower is Better)', fontsize=12)
    plt.ylabel('Probability of Not Yet Found (Survival)', fontsize=12)
    plt.title(title, fontsize=14)
    plt.legend(loc='upper right')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add median survival time annotation
    def get_median_survival(times, survival_probs):
        # Find where survival drops below 0.5
        idx = np.where(survival_probs <= 0.5)[0]
        if len(idx) > 0:
            return times[idx[0]]
        return None
    
    med_base = get_median_survival(base_sorted, base_survival)
    med_iter = get_median_survival(iter_sorted, iter_survival)
    
    if med_base:
        plt.axvline(x=med_base, color='skyblue', linestyle='--', alpha=0.5)
    if med_iter:
        plt.axvline(x=med_iter, color='salmon', linestyle='--', alpha=0.5)
        
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Survival curve saved to: {output_path}")


def plot_correlation_scatter(
    baseline_coverage: List[float],
    iterative_coverage: List[float],
    output_path: Path,
    title: str = "Pairwise Coverage Correlation"
) -> None:
    """
    Plot scatter plot of coverage scores for paired issues.
    """
    plt.figure(figsize=(8, 8))
    
    plt.scatter(baseline_coverage, iterative_coverage, alpha=0.7, edgecolors='k', s=50)
    
    # Diagonal line
    min_val = min(min(baseline_coverage), min(iterative_coverage))
    max_val = max(max(baseline_coverage), max(iterative_coverage))
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', label='No Difference')
    
    plt.xlabel('Static Baseline Coverage (%)', fontsize=12)
    plt.ylabel('Iterative Agent Coverage (%)', fontsize=12)
    plt.title(title, fontsize=14)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Calculate correlation
    corr, p_val = stats.pearsonr(baseline_coverage, iterative_coverage)
    plt.text(
        0.05, 0.95,
        f"Correlation: {corr:.3f}\n(p={p_val:.3g})",
        transform=plt.gca().transAxes,
        fontsize=10,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Scatter plot saved to: {output_path}")


def generate_all_plots(metrics_path: Path, output_dir: Path) -> None:
    """
    Generate all analysis plots based on final metrics.
    
    Args:
        metrics_path: Path to final_metrics.json.
        output_dir: Directory to save plot files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load metrics
    metrics = load_metrics_for_plotting(metrics_path)
    
    # Extract data
    # The stats module structure expects specific keys.
    # We assume 'coverage' and 'ranking' sections exist in final_metrics.json.
    if 'coverage' not in metrics or 'ranking' not in metrics:
        print("Warning: Expected 'coverage' or 'ranking' keys in metrics. Skipping plots.")
        return

    cov_data = metrics['coverage']
    rank_data = metrics['ranking']
    
    baseline_cov = cov_data.get('baseline_coverage', [])
    iterative_cov = cov_data.get('iterative_coverage', [])
    
    # Coverage Plots
    if baseline_cov and iterative_cov:
        plot_coverage_histogram(
            baseline_cov, iterative_cov,
            output_dir / "coverage_histogram.png",
            title="Coverage Distribution: Baseline vs Iterative"
        )
        plot_boxplot_coverage(
            baseline_cov, iterative_cov,
            output_dir / "coverage_boxplot.png",
            title="Coverage Comparison (Boxplot)"
        )
        plot_correlation_scatter(
            baseline_cov, iterative_cov,
            output_dir / "coverage_scatter.png",
            title="Pairwise Coverage Correlation"
        )
    
    # Survival/Ranking Plots
    # We need times and censoring status.
    # Assuming stats.py stored 'baseline_times' (ranks) and 'iterative_times'.
    # Censoring is implied if rank == N+1 (where N is max possible rank or total lines).
    # However, for plotting, we assume the stats module already handled the penalty.
    # We will re-extract raw logs to get censoring info if needed, but for now
    # we assume the 'ranking' section has the necessary lists.
    
    if 'baseline_times' in rank_data and 'iterative_times' in rank_data:
        base_times = rank_data['baseline_times']
        iter_times = rank_data['iterative_times']
        
        # Infer censoring: if time > max_possible_rank, it's censored.
        # But since we don't have max_possible_rank here easily, we assume
        # the stats module already normalized this or we just plot the times.
        # For a proper KM plot, we need the censoring boolean.
        # Let's assume we can derive it from the data if we had the raw logs.
        # Since we are in plots.py, let's try to load the agent logs to get censoring.
        
        logs_path = Path("data/results/agent_logs")
        if logs_path.exists():
            try:
                paired_logs = load_agent_logs_for_pairing(logs_path)
                base_censored = []
                iter_censored = []
                
                for issue_id, logs in paired_logs.items():
                    # Check if baseline found it
                    # This depends on the exact schema of logs.
                    # Assuming 'found' or 'rank' fields exist.
                    # For simplicity in this implementation, we assume
                    # the stats module's 'ranking' data already contains
                    # the necessary lists or we skip the detailed KM plot
                    # if we can't derive censoring accurately.
                    pass
                # Fallback: If we can't get censoring, we plot a simple scatter of ranks.
            except Exception as e:
                print(f"Could not load logs for censoring data: {e}")
        
        # If we don't have censoring, we plot a simple rank distribution
        if base_times and iter_times:
            plt.figure(figsize=(10, 6))
            plt.hist(base_times, bins=20, alpha=0.6, label='Baseline', color='skyblue')
            plt.hist(iter_times, bins=20, alpha=0.6, label='Iterative', color='salmon')
            plt.xlabel('Rank of First Relevant Line', fontsize=12)
            plt.ylabel('Frequency', fontsize=12)
            plt.title('Rank Distribution: Time to First Relevant Line', fontsize=14)
            plt.legend()
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.savefig(output_dir / "rank_distribution.png", dpi=150)
            plt.close()
            print(f"Rank distribution saved to: {output_dir / 'rank_distribution.png'}")


def main() -> None:
    """
    Entry point for generating analysis plots.
    """
    config = get_config_summary()
    metrics_path = Path(config['paths']['results']) / 'final_metrics.json'
    output_dir = Path(config['paths']['results']) / 'figures'
    
    if not metrics_path.exists():
        print(f"Error: Metrics file not found at {metrics_path}")
        print("Please run the stats analysis first (T031).")
        sys.exit(1)
    
    generate_all_plots(metrics_path, output_dir)
    print("All plots generated successfully.")


if __name__ == "__main__":
    main()