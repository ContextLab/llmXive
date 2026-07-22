import json
import math
import sys
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np

from visualization.memory_monitor import check_memory_usage, get_memory_threshold_mb
from utils.logger import get_logger

logger = get_logger(__name__)


def load_analysis_results(results_path: str) -> Dict[str, Any]:
    """Load the meta-analysis results JSON."""
    p = Path(results_path)
    if not p.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_effect_sizes_for_plotting(
    extracted_studies_path: str
) -> Tuple[List[float], List[float]]:
    """
    Load effect sizes (r) and standard errors (se) from the extracted studies CSV.
    Returns two lists: rs and ses.
    """
    import csv
    rs = []
    ses = []
    p = Path(extracted_studies_path)
    if not p.exists():
        raise FileNotFoundError(f"Extracted studies file not found: {extracted_studies_path}")

    with open(p, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            r_val = row.get('r')
            n_val = row.get('n')
            if r_val is not None and n_val is not None:
                try:
                    r_float = float(r_val)
                    n_int = int(n_val)
                    if n_int > 0:
                        # Standard error for correlation coefficient r
                        # SE_r = sqrt((1 - r^2) / (n - 2))
                        se = math.sqrt((1 - r_float**2) / (n_int - 2))
                        rs.append(r_float)
                        ses.append(se)
                except (ValueError, ZeroDivisionError):
                    continue
    return rs, ses


def calculate_pooled_effect(results: Dict[str, Any]) -> float:
    """Extract the pooled effect size (weighted_mean_r) from results."""
    if 'weighted_mean_r' in results:
        return float(results['weighted_mean_r'])
    # Fallback if key is named differently or missing
    logger.warning("weighted_mean_r not found in results, defaulting to 0.0")
    return 0.0


def create_funnel_plot(
    rs: List[float],
    ses: List[float],
    pooled_effect: float,
    output_path: str,
    title: str = "Funnel Plot: Effect Size vs Standard Error"
) -> None:
    """
    Generate and save a funnel plot.
    X-axis: Effect Size (r)
    Y-axis: Standard Error (se)
    Vertical line: Pooled effect (symmetry line)
    """
    if not rs or not ses:
        raise ValueError("No valid effect sizes or standard errors to plot.")

    # Memory check before heavy plotting
    check_memory_usage("Funnel Plot Generation")

    plt.figure(figsize=(10, 8))

    # Scatter plot of studies
    plt.scatter(rs, ses, color='blue', alpha=0.6, edgecolors='black', label='Studies')

    # Vertical symmetry line at pooled effect
    plt.axvline(x=pooled_effect, color='red', linestyle='--', linewidth=2, label=f'Pooled Effect ({pooled_effect:.3f})')

    # Labels and Title
    plt.xlabel('Effect Size (r)')
    plt.ylabel('Standard Error')
    plt.title(title)
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.6)

    # Invert Y-axis for standard funnel plot appearance (SE decreases upwards)
    # Usually funnel plots have SE on Y, with 0 at top or bottom.
    # Standard convention: 0 SE at top (infinite precision), larger SE at bottom.
    # So we invert Y to put 0 at top.
    plt.gca().invert_yaxis()

    # Ensure output directory exists
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Save with high quality but reasonable size
    plt.savefig(out_path, dpi=150, bbox_inches='tight', format='png')
    plt.close()

    logger.info(f"Funnel plot saved to {output_path}")


def run_funnel_plot_generation(
    results_path: str = "data/derived/results.json",
    extracted_studies_path: str = "data/processed/extracted_studies.csv",
    output_path: str = "data/derived/funnel_plot.png"
) -> None:
    """
    Orchestrates the loading of data and generation of the funnel plot.
    """
    logger.info("Starting Funnel Plot generation...")

    # Load results to get pooled effect
    results = load_analysis_results(results_path)
    pooled_effect = calculate_pooled_effect(results)

    # Load effect sizes and SEs
    rs, ses = load_effect_sizes_for_plotting(extracted_studies_path)

    if not rs:
        logger.warning("No valid data points found for funnel plot. Skipping generation.")
        # Create an empty placeholder or raise? Spec says generate artifact.
        # We will raise to fail loudly if data is missing, as per constraints.
        raise ValueError("Cannot generate funnel plot: No valid effect sizes found in extracted studies.")

    # Generate plot
    create_funnel_plot(rs, ses, pooled_effect, output_path)

    logger.info("Funnel Plot generation completed successfully.")


def main() -> None:
    """Entry point for script execution."""
    # Default paths relative to project root
    results_path = "data/derived/results.json"
    extracted_studies_path = "data/processed/extracted_studies.csv"
    output_path = "data/derived/funnel_plot.png"

    try:
        run_funnel_plot_generation(results_path, extracted_studies_path, output_path)
    except Exception as e:
        logger.error(f"Funnel plot generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()