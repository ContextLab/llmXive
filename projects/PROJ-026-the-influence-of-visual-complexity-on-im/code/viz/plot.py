"""
Visualization module for plotting analysis results.
"""
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path
import numpy as np

from config import get_project_root, get_data_path
from utils.logging import get_logger

logger = get_logger(__name__)

def load_permutation_results() -> Dict[str, Any]:
    """Load permutation test results from JSON."""
    project_root = get_project_root()
    results_path = project_root / "data" / "results" / "permutation_results.json"
    
    if not results_path.exists():
        raise FileNotFoundError(f"Permutation results not found: {results_path}")
    
    import json
    with open(results_path, "r") as f:
        return json.load(f)

def load_aggregated_d_scores() -> pd.DataFrame:
    """Load aggregated D-scores from CSV."""
    project_root = get_project_root()
    data_path = get_data_path()
    scores_path = data_path / "processed" / "aggregated_d_scores.csv"
    
    if not scores_path.exists():
        raise FileNotFoundError(f"Aggregated D-scores not found: {scores_path}")
    
    return pd.read_csv(scores_path)

def plot_boxplot(
    output_path: Optional[Path] = None,
    confidence_level: float = 0.95
) -> None:
    """
    Create a publication-quality boxplot of D-scores by complexity condition.
    
    Args:
        output_path: Path to save the plot. Defaults to data/results/d_score_comparison.png.
        confidence_level: Confidence level for error bars (default 0.95).
    """
    project_root = get_project_root()
    if output_path is None:
        output_path = project_root / "data" / "results" / "d_score_comparison.png"
    
    # Load data
    df = load_aggregated_d_scores()
    
    # Filter valid scores
    valid_df = df[df["status"] == "valid"].copy()
    
    if valid_df.empty:
        logger.warning("No valid D-scores found for plotting.")
        return
    
    # Set style
    sns.set_theme(style="whitegrid", font="Arial")
    
    # Create figure
    plt.figure(figsize=(10, 6), dpi=300)
    
    # Plot boxplot
    ax = sns.boxplot(
        x="complexity_condition",
        y="d_score",
        data=valid_df,
        palette="viridis",
        linewidth=1.5,
        fliersize=3
    )
    
    # Add jittered points for individual data
    sns.stripplot(
        x="complexity_condition",
        y="d_score",
        data=valid_df,
        color="black",
        alpha=0.5,
        size=4,
        jitter=True
    )
    
    # Add mean points
    means = valid_df.groupby("complexity_condition")["d_score"].mean().reset_index()
    sns.scatterplot(
        x="complexity_condition",
        y="d_score",
        data=means,
        color="red",
        s=100,
        marker="D",
        label="Mean",
        zorder=10
    )
    
    # Add error bars (95% CI)
    ci_data = valid_df.groupby("complexity_condition")["d_score"].agg(
        mean="mean",
        sem="sem",
        count="count"
    ).reset_index()
    
    # Calculate 95% CI
    from scipy.stats import t
    ci_data["ci"] = t.ppf((1 + confidence_level) / 2, ci_data["count"] - 1) * ci_data["sem"]
    
    for idx, row in ci_data.iterrows():
        ax.errorbar(
            x=row["complexity_condition"],
            y=row["mean"],
            yerr=row["ci"],
            color="red",
            fmt="none",
            capsize=5,
            linewidth=2,
            zorder=9
        )
    
    # Labels and title
    plt.xlabel("Complexity Condition", fontsize=12, fontfamily="Arial")
    plt.ylabel("D-Score (IAT Effect)", fontsize=12, fontfamily="Arial")
    plt.title("Implicit Bias by Visual Complexity Condition", fontsize=14, fontfamily="Arial")
    
    # Legend
    plt.legend(loc="upper right", fontsize=10, frameon=True)
    
    # Tight layout
    plt.tight_layout()
    
    # Save
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    plt.close()
    
    logger.info(f"Boxplot saved to {output_path}")

def plot_sensitivity(
    sensitivity_results: Dict[str, Any],
    output_path: Optional[Path] = None
) -> None:
    """
    Plot sensitivity analysis results.
    
    Args:
        sensitivity_results: Dictionary containing threshold sweep and LOIO results.
        output_path: Path to save the plot.
    """
    if output_path is None:
        project_root = get_project_root()
        output_path = project_root / "data" / "results" / "sensitivity_analysis.png"
    
    threshold_sweep = sensitivity_results.get("threshold_sweep", [])
    if not threshold_sweep:
        logger.warning("No threshold sweep data for sensitivity plot.")
        return
    
    df = pd.DataFrame(threshold_sweep)
    
    plt.figure(figsize=(10, 6), dpi=300)
    sns.lineplot(
        x="threshold_shift",
        y="p_value",
        data=df,
        marker="o",
        linewidth=2,
        markersize=8
    )
    
    plt.axhline(y=0.05, color="red", linestyle="--", label="Significance Threshold (0.05)")
    plt.xlabel("Threshold Shift (SD units)", fontsize=12, fontfamily="Arial")
    plt.ylabel("P-Value", fontsize=12, fontfamily="Arial")
    plt.title("Sensitivity Analysis: Threshold Sweep", fontsize=14, fontfamily="Arial")
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    plt.close()
    
    logger.info(f"Sensitivity plot saved to {output_path}")

def plot_loio_sensitivity(
    sensitivity_results: Dict[str, Any],
    output_path: Optional[Path] = None
) -> None:
    """
    Plot LOIO sensitivity analysis results.
    
    Args:
        sensitivity_results: Dictionary containing LOIO results.
        output_path: Path to save the plot.
    """
    if output_path is None:
        project_root = get_project_root()
        output_path = project_root / "data" / "results" / "loio_sensitivity.png"
    
    loio_results = sensitivity_results.get("loio_results", [])
    if not loio_results:
        logger.warning("No LOIO data for sensitivity plot.")
        return
    
    df = pd.DataFrame(loio_results)
    
    plt.figure(figsize=(10, 6), dpi=300)
    sns.barplot(
        x="image_index",
        y="p_value",
        data=df,
        palette="viridis",
        edgecolor="black"
    )
    
    plt.axhline(y=0.05, color="red", linestyle="--", label="Significance Threshold (0.05)")
    plt.xlabel("Excluded Image Index", fontsize=12, fontfamily="Arial")
    plt.ylabel("P-Value", fontsize=12, fontfamily="Arial")
    plt.title("Leave-One-Image-Out Sensitivity Analysis", fontsize=14, fontfamily="Arial")
    plt.legend(fontsize=10)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    plt.close()
    
    logger.info(f"LOIO sensitivity plot saved to {output_path}")

def main() -> None:
    """
    Main entry point for plotting.
    Generates all required plots.
    """
    logger.info("Starting visualization...")
    
    project_root = get_project_root()
    results_dir = project_root / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Plot 1: D-Score Comparison Boxplot (T037)
    plot_boxplot(output_path=results_dir / "d_score_comparison.png")
    
    # Plot 2: Sensitivity Analysis
    try:
        import json
        with open(results_dir / "sensitivity_results.json", "r") as f:
            sensitivity_results = json.load(f)
        
        plot_sensitivity(sensitivity_results, output_path=results_dir / "sensitivity_analysis.png")
        plot_loio_sensitivity(sensitivity_results, output_path=results_dir / "loio_sensitivity.png")
    except FileNotFoundError:
        logger.warning("Sensitivity results not found. Skipping sensitivity plots.")
    
    logger.info("Visualization completed.")

if __name__ == "__main__":
    main()
