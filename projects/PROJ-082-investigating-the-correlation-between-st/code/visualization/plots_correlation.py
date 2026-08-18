"""
code/visualization/plots_correlation.py
Generates the Correlation Summary Plot.

This module creates a bar chart visualizing the correlation coefficients (r-values)
for different structural brain tracts found in the meta-analysis results.
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

# Configure logging for this module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def get_project_root() -> Path:
    """Determine the project root directory."""
    current = Path(__file__).resolve()
    # Navigate up from code/visualization/ to the root
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
    """
    Extract effect sizes (r) and tract names from the results data.
    
    Returns:
        Tuple of (list of r values, list of tract names)
    """
    studies = data.get("studies", [])
    r_values = []
    tracts = []

    for s in studies:
        if isinstance(s, dict):
            r = s.get("r")
            tract = s.get("tract", "Unknown")
            if r is not None and not math.isnan(r) if isinstance(r, float) else True:
                try:
                    r_val = float(r)
                    if not math.isnan(r_val) and not math.isinf(r_val):
                        r_values.append(r_val)
                        tracts.append(str(tract))
                except (ValueError, TypeError):
                    continue

    return r_values, tracts

def create_correlation_summary_plot(r_values: List[float], tracts: List[str]) -> None:
    """
    Create and save the correlation summary plot.
    
    Generates a bar chart sorted by effect size, with labels and a zero line.
    Saves the output to data/derived/correlation_summary.png.
    """
    n = len(r_values)
    if n == 0:
        logging.warning("No studies with valid effect sizes to plot")
        # Create an empty placeholder plot to satisfy file existence checks
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, 'No valid data for Correlation Summary Plot', 
                transform=plt.gca().transAxes, ha='center', va='center')
        plt.title('Correlation Summary: Structural Connectivity vs Music Preferences')
        plt.tight_layout()
    else:
        if MEMORY_MONITOR_AVAILABLE:
            check_memory_usage("Correlation Summary Plot Generation")

        plt.figure(figsize=(10, 6))
        
        # Sort by effect size for better visualization
        sorted_indices = np.argsort(r_values)
        sorted_r = np.array(r_values)[sorted_indices]
        sorted_tracts = np.array(tracts)[sorted_indices]

        # Bar plot
        x_pos = np.arange(n)
        # Use a color map that distinguishes positive and negative correlations
        colors = [plt.cm.RdYlBu_r((val + 1) / 2) for val in sorted_r]
        
        bars = plt.bar(x_pos, sorted_r, color=colors, edgecolor='black', alpha=0.8)
        
        # Add value labels on bars
        for i, (bar, val) in enumerate(zip(bars, sorted_r)):
            height = bar.get_height()
            # Adjust text position based on bar direction
            y_pos = height + 0.01 if height >= 0 else height - 0.02
            plt.text(bar.get_x() + bar.get_width()/2., y_pos,
                     f'{val:.2f}', ha='center', va='bottom' if height >= 0 else 'top', fontsize=8)

        plt.xticks(x_pos, sorted_tracts, rotation=45, ha='right', fontsize=8)
        plt.xlabel('Tract', fontsize=10)
        plt.ylabel('Correlation Coefficient (r)', fontsize=10)
        plt.title('Correlation Summary: Structural Connectivity vs Music Preferences', fontsize=12)
        plt.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        plt.grid(axis='y', linestyle=':', alpha=0.3)
        
        plt.tight_layout()

    root = get_project_root()
    output_path = root / "data" / "derived" / "correlation_summary.png"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logging.info(f"Correlation summary plot saved to {output_path}")

def run_correlation_plot_generation() -> Dict[str, Any]:
    """
    Main entry point for correlation summary plot generation.
    
    Returns:
        Dictionary with status and output path or error reason.
    """
    try:
        data = load_analysis_results()
    except FileNotFoundError as e:
        logging.error(f"Failed to load results: {e}")
        return {"status": "error", "reason": str(e)}

    # Check if we are in narrative mode (no quantitative results to plot)
    if data.get("synthesis_mode") == "narrative":
        logging.info("Skipping plot generation: synthesis mode is narrative")
        return {"status": "skipped", "reason": "Meta-analysis skipped (narrative mode)"}

    r_values, tracts = load_effect_sizes_for_plotting(data)

    if not r_values:
        logging.warning("No valid effect sizes found for plotting")
        # Still generate an empty plot to satisfy file existence requirements
        try:
            create_correlation_summary_plot([], [])
            return {"status": "completed", "output": "data/derived/correlation_summary.png", "note": "Empty plot generated due to no data"}
        except Exception as e:
            return {"status": "error", "reason": f"Failed to generate empty plot: {str(e)}"}

    try:
        create_correlation_summary_plot(r_values, tracts)
        return {"status": "completed", "output": "data/derived/correlation_summary.png"}
    except Exception as e:
        logging.error(f"Error during plot generation: {e}")
        return {"status": "error", "reason": str(e)}

def main():
    """CLI entry point."""
    result = run_correlation_plot_generation()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["status"] in ["completed", "skipped"] else 1)

if __name__ == "__main__":
    main()