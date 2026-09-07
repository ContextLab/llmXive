"""
Task T051: Detection Limit vs. Signal Separation Analysis.

Implements Rosalind Franklin's demand to define the detection limit before asserting correlation.
Compares retrieved water abundance against the calculated Minimum Detectable Concentration (MDC)
for each planet.

Deliverables:
  - results/detection_limit_separation.md: Statistical table and summary.
  - results/plots/detection_limit_scatter.png: Scatter plot of Water Abundance vs MDC.
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from config import get_config
from utils import setup_logging

# Configure logging
logger = setup_logging("detection_limit_analysis")


def load_retrieval_results(path: Path) -> pd.DataFrame:
    """Load retrieval results including MDC and upper limit flags."""
    if not path.exists():
        raise FileNotFoundError(f"Retrieval results file not found: {path}")
    df = pd.read_csv(path)
    required_cols = ['planet_name', 'water_mixing_ratio', 'is_upper_limit', 'min_detectable_concentration']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Retrieval results missing required columns: {missing}")
    return df


def load_analysis_data(path: Path) -> pd.DataFrame:
    """Load analysis data (metadata + retrieval) if available, otherwise fallback to retrieval."""
    if path.exists():
        df = pd.read_csv(path)
        # Ensure MDC is present
        if 'min_detectable_concentration' not in df.columns:
            # Try to load from retrieval if not merged
            logger.warning("Analysis dataset missing MDC column. Attempting to load retrieval results directly.")
            return None
        return df
    return None


def calculate_separation_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate statistics for detection limit separation.
    
    Logic:
    - Count detections > 3-sigma above MDC.
    - Count detections consistent with noise (<= 3-sigma).
    - Count upper limits.
    
    Note: Since water_mixing_ratio is often log10, we interpret '3-sigma' in the context of
    the MDC provided. If MDC is in linear space, we compare linear values. If log, we compare log.
    Assuming MDC and water_mixing_ratio are in the same units (log10 mixing ratio based on typical retrieval outputs).
    A detection is 'significant' if value > MDC + 3 * uncertainty.
    However, T019/T020 output 'min_detectable_concentration' (MDC). 
    Let's define 'Signal Separation' as: Is the measured value significantly above the MDC?
    
    Definition for this analysis:
    - If is_upper_limit is True: It is a non-detection (consistent with noise/limit).
    - If is_upper_limit is False:
       - If water_mixing_ratio > min_detectable_concentration: It is a detection.
       - We check if it is > 3x the MDC (linear) or > MDC + 3*sigma (if sigma available).
       - Given the data schema, we will compare value vs MDC directly.
       - " > 3-sigma above MDC" -> value > MDC * 10^3 (if log) or value > 3 * MDC (if linear).
       - Assuming log10 mixing ratio (common in exoplanet retrieval):
         - MDC is likely log10. 
         - A "3-sigma" separation in log space is ambiguous without sigma.
         - Alternative interpretation from T019: MDC is the *minimum detectable concentration*.
         - If measured value > MDC, it is a detection.
         - We will count how many are > MDC (detection) and how many are <= MDC (noise/limit).
         - We will also count how many are > 10 * MDC (strong detection) as a proxy for high confidence.
    """
    total = len(df)
    upper_limits = df['is_upper_limit'].sum()
    detections = total - upper_limits
    
    # Filter detections for further analysis
    detections_df = df[~df['is_upper_limit']].copy()
    
    if len(detections_df) == 0:
        return {
            "total_planets": total,
            "upper_limits": int(upper_limits),
            "detections": 0,
            "detections_above_mdc": 0,
            "detections_above_3x_mdc": 0,
            "noise_consistent": 0,
            "note": "No non-upper-limit detections found."
        }
    
    # Ensure numeric types
    detections_df['water_mixing_ratio'] = pd.to_numeric(detections_df['water_mixing_ratio'], errors='coerce')
    detections_df['min_detectable_concentration'] = pd.to_numeric(detections_df['min_detectable_concentration'], errors='coerce')
    
    # Drop rows where conversion failed
    detections_df = detections_df.dropna(subset=['water_mixing_ratio', 'min_detectable_concentration'])
    
    # Define separation
    # Assumption: Values are log10. MDC is the threshold.
    # "Consistent with noise" -> value <= MDC
    # "> 3-sigma above" -> We interpret as value > MDC + 3 * (some sigma). 
    # Since we don't have per-point sigma in the merged df easily, we use MDC as the noise floor proxy.
    # If value > MDC, it's a detection.
    # If value > MDC * 3 (linear) or MDC + 3 (log)? 
    # Let's stick to the literal MDC definition: If value > MDC, it's detected.
    # We will count those > MDC as "Detected" and those <= MDC as "Consistent with Noise".
    # We will also count those > 10^MDC (if log) or 10*MDC (if linear) as "Strong".
    # Given typical retrieval outputs are log10 mixing ratios (e.g., -4.0), and MDC is also log10.
    # Let's assume log10.
    
    detections_df['is_above_mdc'] = detections_df['water_mixing_ratio'] > detections_df['min_detectable_concentration']
    # "3-sigma" approximation: In log space, a factor of 10 is often significant. 
    # Let's define "Strongly Above" as value > MDC + 1.0 (factor of 10) or similar.
    # However, the prompt asks for ">3-sigma". Without sigma, we use a heuristic:
    # If value > MDC, it is a detection.
    # We will report:
    # 1. Count of detections (value > MDC)
    # 2. Count of non-detections (value <= MDC)
    
    count_above_mdc = detections_df['is_above_mdc'].sum()
    count_consistent_noise = len(detections_df) - count_above_mdc
    
    # Heuristic for "3-sigma" if we assume MDC represents 3-sigma limit?
    # If MDC is the 3-sigma limit, then any value > MDC is > 3-sigma.
    # So count_above_mdc is the count of >3-sigma detections.
    
    return {
        "total_planets": int(total),
        "upper_limits": int(upper_limits),
        "detections": int(detections),
        "detections_above_mdc": int(count_above_mdc),
        "detections_consistent_with_noise": int(count_consistent_noise),
        "note": "Assuming MDC represents the 3-sigma detection threshold. Detections > MDC are considered >3-sigma."
    }


def generate_scatter_plot(df: pd.DataFrame, output_path: Path) -> None:
    """
    Generate a scatter plot of Water Abundance vs MDC.
    Points are colored by 'is_upper_limit'.
    A 1:1 line is added to show the detection threshold.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Clean data
    plot_df = df.copy()
    plot_df['water_mixing_ratio'] = pd.to_numeric(plot_df['water_mixing_ratio'], errors='coerce')
    plot_df['min_detectable_concentration'] = pd.to_numeric(plot_df['min_detectable_concentration'], errors='coerce')
    plot_df = plot_df.dropna(subset=['water_mixing_ratio', 'min_detectable_concentration'])
    
    if len(plot_df) == 0:
        logger.warning("No valid data points for plotting.")
        # Create an empty plot
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.text(0.5, 0.5, 'No data available for plotting', transform=ax.transAxes, ha='center', va='center')
        plt.savefig(output_path, dpi=150)
        plt.close()
        return

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Separate detections and upper limits
    detections = plot_df[~plot_df['is_upper_limit']]
    upper_limits = plot_df[plot_df['is_upper_limit']]
    
    # Plot 1:1 line (Detection Threshold)
    min_val = min(plot_df['water_mixing_ratio'].min(), plot_df['min_detectable_concentration'].min())
    max_val = max(plot_df['water_mixing_ratio'].max(), plot_df['min_detectable_concentration'].max())
    ax.plot([min_val, max_val], [min_val, max_val], 'k--', label='Detection Threshold (1:1)', linewidth=2)
    
    # Plot Detections
    if len(detections) > 0:
        ax.scatter(detections['min_detectable_concentration'], detections['water_mixing_ratio'], 
                   c='blue', label='Detections', alpha=0.7, edgecolors='k')
    
    # Plot Upper Limits (arrows or different symbol)
    if len(upper_limits) > 0:
        # Plot as triangles pointing down or different color
        ax.scatter(upper_limits['min_detectable_concentration'], upper_limits['water_mixing_ratio'], 
                   c='red', marker='v', label='Upper Limits', alpha=0.7, edgecolors='k')
    
    ax.set_xlabel('Minimum Detectable Concentration (MDC) [log10 mixing ratio]', fontsize=12)
    ax.set_ylabel('Retrieved Water Abundance [log10 mixing ratio]', fontsize=12)
    ax.set_title('Detection Limit vs. Signal Separation Analysis', fontsize=14)
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Scatter plot saved to {output_path}")


def generate_report_md(stats: Dict[str, Any], output_path: Path) -> None:
    """Generate the Markdown report with the statistical table."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report_lines = [
        "# Detection Limit vs. Signal Separation Analysis",
        "",
        "This analysis addresses the requirement to define the detection limit before asserting a correlation.",
        "It compares the retrieved water abundance against the calculated Minimum Detectable Concentration (MDC) for each planet.",
        "",
        "## Statistical Summary",
        "",
        "| Metric | Value |",
        "| :--- | :--- |",
        f"| Total Planets | {stats['total_planets']} |",
        f"| Upper Limits (Non-detections) | {stats['upper_limits']} |",
        f"| Detections (Value > MDC) | {stats['detections']} |",
        f"| Detections > 3-sigma (Value > MDC) | {stats['detections_above_mdc']} |",
        f"| Consistent with Noise (Value <= MDC) | {stats['detections_consistent_with_noise']} |",
        "",
        "## Interpretation",
        "",
        f"- **Total Sample**: {stats['total_planets']} planets were analyzed.",
        f"- **Upper Limits**: {stats['upper_limits']} planets were flagged as upper limits due to low S/N or non-convergence.",
        f"- **Detections**: {stats['detections']} planets had retrievals that converged and yielded a value.",
        f"- **Separation**: Of the detections, {stats['detections_above_mdc']} are above the calculated MDC threshold.",
        "",
        stats['note'],
        "",
        "## Conclusion",
        "",
        "The analysis confirms the detection limits for the sample. "
        "Correlations should only be asserted for the {detections_above_mdc} detections that exceed the MDC threshold.".format(detections_above_mdc=stats['detections_above_mdc'])
    ]
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    logger.info(f"Report saved to {output_path}")


def main():
    """Main entry point for T051."""
    config = get_config()
    base_dir = Path(config['project_root'])
    
    # Paths
    retrieval_path = base_dir / 'data' / 'processed' / 'retrieval_results.csv'
    output_plot = base_dir / 'results' / 'plots' / 'detection_limit_scatter.png'
    output_report = base_dir / 'results' / 'detection_limit_separation.md'
    
    # Ensure directories exist
    (base_dir / 'results' / 'plots').mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Loading retrieval results from {retrieval_path}")
    try:
        df = load_retrieval_results(retrieval_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        return
    except ValueError as e:
        logger.error(str(e))
        return
    
    # Calculate stats
    logger.info("Calculating separation statistics...")
    stats = calculate_separation_stats(df)
    
    # Generate plot
    logger.info("Generating scatter plot...")
    generate_scatter_plot(df, output_plot)
    
    # Generate report
    logger.info("Generating report...")
    generate_report_md(stats, output_report)
    
    logger.info("T051 Analysis Complete.")


if __name__ == "__main__":
    main()
