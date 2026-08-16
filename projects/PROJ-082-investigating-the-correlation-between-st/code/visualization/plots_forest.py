"""
code/visualization/plots_forest.py
Generates the Forest Plot for meta-analysis results.
"""
import json
import math
import sys
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# Import memory monitor if available
try:
    from visualization.memory_monitor import check_memory_usage, get_memory_threshold_mb
    MEMORY_MONITOR_AVAILABLE = True
except ImportError:
    MEMORY_MONITOR_AVAILABLE = False

def get_project_root() -> Path:
    """Determine the project root directory."""
    current = Path(__file__).resolve()
    if "code" in current.parts:
        return current.parents[1]
    return current.parent.parent

def load_analysis_results() -> Dict[str, Any]:
    """Load results from data/derived/results.json."""
    root = get_project_root()
    path = root / "data" / "derived" / "results.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing results file: {path}")
    with open(path, "r") as f:
        return json.load(f)

def load_effect_sizes_for_plotting(data: Dict[str, Any]) -> Tuple[List[float], List[float], List[str]]:
    """
    Extract effect sizes, standard errors, and labels from results.
    Returns (r_values, se_values, labels).
    """
    studies = data.get("studies", [])
    r_values = []
    se_values = []
    labels = []

    for i, s in enumerate(studies):
        if isinstance(s, dict):
            r = s.get("r")
            se = s.get("se")
            author = s.get("author", f"Study {i+1}")
            year = s.get("year", "")
            if r is not None and se is not None:
                r_values.append(float(r))
                se_values.append(float(se))
                labels.append(f"{author} ({year})")

    return r_values, se_values, labels

def calculate_ci(r: float, se: float, alpha: float = 0.05) -> Tuple[float, float]:
    """Calculate 95% confidence interval for an effect size."""
    z = 1.96  # Approximate for 95% CI
    lower = r - z * se
    upper = r + z * se
    return lower, upper

def create_forest_plot(r_values: List[float], se_values: List[float], labels: List[str], 
                       weighted_mean_r: float, ci_lower: float, ci_upper: float) -> None:
    """
    Create and save the forest plot.
    """
    n = len(r_values)
    if n == 0:
        logging.warning("No studies to plot")
        return

    # Check memory if monitor available
    if MEMORY_MONITOR_AVAILABLE:
        check_memory_usage("Forest Plot Generation")

    # Calculate figure height dynamically based on number of studies
    # Ensure minimum height of 6, plus 0.4 inches per study
    fig_height = max(6, n * 0.4)
    plt.figure(figsize=(10, fig_height))
    
    # Plot individual studies
    y_positions = range(n)
    errors = np.array(se_values) * 1.96  # 95% CI width

    plt.errorbar(r_values, y_positions, xerr=errors, fmt='o', capsize=5, 
                 ecolor='gray', elinewidth=1, markerfacecolor='blue', 
                 markersize=6, label='Studies')

    # Plot summary diamond
    # Use a distinct marker to represent the summary effect
    summary_y = -0.5
    plt.plot([weighted_mean_r, weighted_mean_r], [summary_y - 0.2, summary_y + 0.2], 
             'D-', color='red', markersize=15, markeredgewidth=2, 
             markeredgecolor='darkred', label='Summary (Weighted Mean)')
    
    # Draw CI line for summary
    plt.plot([ci_lower, ci_upper], [summary_y, summary_y], 'r-', linewidth=2)

    # Labels and formatting
    plt.yticks(y_positions, labels, fontsize=8)
    plt.xlabel('Effect Size (r)', fontsize=10)
    plt.title('Forest Plot: Structural Connectivity and Music Preferences', fontsize=12)
    plt.axvline(x=0, color='black', linestyle='--', linewidth=0.5)
    plt.legend(loc='upper left')
    plt.grid(axis='x', linestyle=':', alpha=0.3)
    
    # Adjust layout to prevent label clipping
    plt.tight_layout()

    # Save plot
    root = get_project_root()
    output_path = root / "data" / "derived" / "forest_plot.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logging.info(f"Forest plot saved to {output_path}")

def run_forest_plot_generation() -> Dict[str, Any]:
    """Main entry point for forest plot generation."""
    try:
        data = load_analysis_results()
    except FileNotFoundError as e:
        return {"status": "error", "reason": str(e)}

    # Check if meta-analysis was skipped (narrative mode)
    if data.get("synthesis_mode") == "narrative":
        return {"status": "skipped", "reason": "Meta-analysis skipped (narrative mode)"}

    weighted_mean_r = data.get("weighted_mean_r")
    if weighted_mean_r is None:
        return {"status": "error", "reason": "No weighted mean r found in results"}

    # Calculate summary CI
    # Approximate SE for summary (inverse variance weighted)
    studies = data.get("studies", [])
    if not studies:
        return {"status": "error", "reason": "No studies found"}
    
    # Simple approximation for summary CI based on inverse variance
    se_sum = sum(1.0 / (s.get("se", 0.1) ** 2) for s in studies if s.get("se"))
    if se_sum > 0:
        summary_se = math.sqrt(1.0 / se_sum)
    else:
        summary_se = 0.1

    ci_lower = weighted_mean_r - 1.96 * summary_se
    ci_upper = weighted_mean_r + 1.96 * summary_se

    r_values, se_values, labels = load_effect_sizes_for_plotting(data)

    if not r_values:
        return {"status": "error", "reason": "No valid effect sizes for plotting"}

    try:
        create_forest_plot(r_values, se_values, labels, weighted_mean_r, ci_lower, ci_upper)
        return {"status": "completed", "output": "data/derived/forest_plot.png"}
    except Exception as e:
        return {"status": "error", "reason": str(e)}

def main():
    """CLI entry point."""
    result = run_forest_plot_generation()
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()