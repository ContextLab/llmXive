"""
code/visualization/plots_correlation.py
Generates the Correlation Summary Plot.
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

try:
    from visualization.memory_monitor import check_memory_usage
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

def load_effect_sizes_for_plotting(data: Dict[str, Any]) -> Tuple[List[float], List[str]]:
    """Extract effect sizes (r) and tract names."""
    studies = data.get("studies", [])
    r_values = []
    tracts = []

    for s in studies:
        if isinstance(s, dict):
            r = s.get("r")
            tract = s.get("tract", "Unknown")
            if r is not None:
                r_values.append(float(r))
                tracts.append(tract)

    return r_values, tracts

def create_correlation_summary_plot(r_values: List[float], tracts: List[str]) -> None:
    """Create and save the correlation summary plot."""
    n = len(r_values)
    if n == 0:
        logging.warning("No studies to plot")
        return

    if MEMORY_MONITOR_AVAILABLE:
        check_memory_usage("Correlation Summary Plot Generation")

    plt.figure(figsize=(10, 6))
    
    # Sort by effect size for better visualization
    sorted_indices = np.argsort(r_values)
    sorted_r = np.array(r_values)[sorted_indices]
    sorted_tracts = np.array(tracts)[sorted_indices]

    # Bar plot
    x_pos = np.arange(n)
    colors = plt.cm.viridis(np.linspace(0, 1, n))
    
    bars = plt.bar(x_pos, sorted_r, color=colors, edgecolor='black', alpha=0.8)
    
    # Add value labels on bars
    for i, (bar, val) in enumerate(zip(bars, sorted_r)):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                 f'{val:.2f}', ha='center', va='bottom', fontsize=8)

    plt.xticks(x_pos, sorted_tracts, rotation=45, ha='right', fontsize=8)
    plt.xlabel('Tract', fontsize=10)
    plt.ylabel('Correlation Coefficient (r)', fontsize=10)
    plt.title('Correlation Summary: Structural Connectivity vs Music Preferences', fontsize=12)
    plt.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    plt.grid(axis='y', linestyle=':', alpha=0.3)
    
    plt.tight_layout()

    root = get_project_root()
    output_path = root / "data" / "derived" / "correlation_summary.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logging.info(f"Correlation summary plot saved to {output_path}")

def run_correlation_plot_generation() -> Dict[str, Any]:
    """Main entry point for correlation summary plot generation."""
    try:
        data = load_analysis_results()
    except FileNotFoundError as e:
        return {"status": "error", "reason": str(e)}

    if data.get("synthesis_mode") == "narrative":
        return {"status": "skipped", "reason": "Meta-analysis skipped (narrative mode)"}

    r_values, tracts = load_effect_sizes_for_plotting(data)

    if not r_values:
        return {"status": "error", "reason": "No valid effect sizes for plotting"}

    try:
        create_correlation_summary_plot(r_values, tracts)
        return {"status": "completed", "output": "data/derived/correlation_summary.png"}
    except Exception as e:
        return {"status": "error", "reason": str(e)}

def main():
    """CLI entry point."""
    result = run_correlation_plot_generation()
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()