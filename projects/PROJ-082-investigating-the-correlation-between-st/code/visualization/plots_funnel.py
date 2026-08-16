"""
code/visualization/plots_funnel.py
Generates the Funnel Plot for publication bias visualization.
Plots Standard Error (Y) vs Effect Size (X) with a symmetry line at the pooled effect.
"""
import json
import math
import sys
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np

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

def load_effect_sizes_for_plotting(data: Dict[str, Any]) -> Tuple[List[float], List[float]]:
    """Extract effect sizes (r) and standard errors (se) from the results JSON."""
    studies = data.get("studies", [])
    r_values = []
    se_values = []

    for s in studies:
        if isinstance(s, dict):
            r = s.get("r")
            se = s.get("se")
            # Ensure we have valid numeric data
            if r is not None and se is not None:
                try:
                    r_val = float(r)
                    se_val = float(se)
                    if not math.isnan(r_val) and not math.isinf(r_val) and se_val > 0:
                        r_values.append(r_val)
                        se_values.append(se_val)
                except (ValueError, TypeError):
                    continue

    return r_values, se_values

def calculate_pooled_effect(r_values: List[float], se_values: List[float]) -> float:
    """Calculate weighted pooled effect size (inverse variance weighting)."""
    if not r_values or not se_values:
        return 0.0
    
    # Inverse variance weights: w = 1 / se^2
    weights = [1.0 / (se ** 2) for se in se_values]
    total_weight = sum(weights)
    
    if total_weight == 0:
        return np.mean(r_values)
    
    weighted_sum = sum(r * w for r, w in zip(r_values, weights))
    return weighted_sum / total_weight

def create_funnel_plot(r_values: List[float], se_values: List[float], 
                       pooled_effect: float) -> None:
    """Create and save the funnel plot to data/derived/funnel_plot.png."""
    n = len(r_values)
    if n == 0:
        logging.warning("No studies to plot for funnel plot.")
        return

    if MEMORY_MONITOR_AVAILABLE:
        check_memory_usage("Funnel Plot Generation")

    plt.figure(figsize=(8, 8))
    
    # Convert to numpy arrays for plotting
    se_arr = np.array(se_values)
    r_arr = np.array(r_values)

    # Plot points: Effect Size (X) vs Standard Error (Y)
    plt.scatter(r_arr, se_arr, alpha=0.6, edgecolors='k', label='Studies', zorder=2)

    # Plot vertical symmetry line at pooled effect
    plt.axvline(x=pooled_effect, color='red', linestyle='--', linewidth=2, 
                label=f'Pooled Effect ({pooled_effect:.3f})', zorder=3)

    # Add pseudo-confidence limits (funnel shape)
    # Calculate 95% CI bounds: pooled ± 1.96 * SE
    se_min = min(se_arr)
    se_max = max(se_arr)
    se_range = np.linspace(se_min, se_max, 100)
    
    z = 1.96
    upper_bound = pooled_effect + z * se_range
    lower_bound = pooled_effect - z * se_range

    plt.plot(upper_bound, se_range, 'r--', alpha=0.5, linewidth=1, zorder=1, label='95% CI')
    plt.plot(lower_bound, se_range, 'r--', alpha=0.5, linewidth=1, zorder=1)

    plt.xlabel('Effect Size (r)', fontsize=12)
    plt.ylabel('Standard Error', fontsize=12)
    plt.title('Funnel Plot: Publication Bias Assessment', fontsize=14)
    plt.legend(loc='upper right')
    plt.grid(True, linestyle=':', alpha=0.3)
    
    # Invert Y axis so smaller SE (more precise) is at the top
    plt.gca().invert_yaxis()

    plt.tight_layout()

    root = get_project_root()
    output_dir = root / "data" / "derived"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "funnel_plot.png"
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logging.info(f"Funnel plot saved to {output_path}")

def run_funnel_plot_generation() -> Dict[str, Any]:
    """Main entry point for funnel plot generation."""
    try:
        data = load_analysis_results()
    except FileNotFoundError as e:
        return {"status": "error", "reason": f"Results file not found: {e}"}

    # Check if we are in narrative mode (no quantitative data to plot)
    if data.get("synthesis_mode") == "narrative":
        return {"status": "skipped", "reason": "Meta-analysis skipped (narrative mode)"}

    r_values, se_values = load_effect_sizes_for_plotting(data)

    if not r_values:
        return {"status": "error", "reason": "No valid effect sizes found for plotting"}

    pooled_effect = calculate_pooled_effect(r_values, se_values)

    try:
        create_funnel_plot(r_values, se_values, pooled_effect)
        return {"status": "completed", "output": "data/derived/funnel_plot.png"}
    except Exception as e:
        logging.error(f"Error generating funnel plot: {e}", exc_info=True)
        return {"status": "error", "reason": str(e)}

def main():
    """CLI entry point."""
    result = run_funnel_plot_generation()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("status") == "completed" else 1)

if __name__ == "__main__":
    main()