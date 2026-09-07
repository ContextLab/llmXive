import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

from config import get_config
from utils import setup_logging

logger = logging.getLogger(__name__)

def load_metadata(metadata_path: str) -> pd.DataFrame:
    """Load the processed metadata CSV."""
    path = Path(metadata_path)
    if not path.exists():
        raise FileNotFoundError(f"Metadata file not found: {path}")
    logger.info(f"Loading metadata from {path}")
    df = pd.read_csv(path)
    # Ensure necessary columns exist
    required_cols = ['planet_name', 'temperature', 'instrument']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column in metadata: {col}")
    return df

def load_retrieval_results(retrieval_path: str) -> pd.DataFrame:
    """Load the retrieval results CSV."""
    path = Path(retrieval_path)
    if not path.exists():
        raise FileNotFoundError(f"Retrieval results file not found: {path}")
    logger.info(f"Loading retrieval results from {path}")
    df = pd.read_csv(path)
    required_cols = ['planet_name', 'water_mixing_ratio', 'is_upper_limit']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column in retrieval results: {col}")
    return df

def bin_temperature(temperatures: pd.Series, bins: List[float] = None) -> pd.Series:
    """
    Bin equilibrium temperatures into discrete categories for comparison.
    Default bins: <1000K (Super-Earth range), 1000-1500K, 1500-2000K, >2000K (Hot Jupiter range).
    """
    if bins is None:
        bins = [0, 1000, 1500, 2000, float('inf')]
    labels = ['<1000K', '1000-1500K', '1500-2000K', '>2000K']
    return pd.cut(temperatures, bins=bins, labels=labels, include_lowest=True)

def analyze_instrument_bias(
    metadata_df: pd.DataFrame,
    retrieval_df: pd.DataFrame,
    temp_bins: List[float] = None
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Analyze systematic biases by instrument.
    Groups planets by instrument and temperature bin, then calculates mean/std of water abundance.
    Flags instruments with high variance or significant mean shifts compared to the global median.
    """
    # Merge data on planet_name
    merged = pd.merge(
        metadata_df[['planet_name', 'temperature', 'instrument']],
        retrieval_df[['planet_name', 'water_mixing_ratio', 'is_upper_limit']],
        on='planet_name',
        how='inner'
    )

    if merged.empty:
        logger.warning("No matching planets found between metadata and retrieval results.")
        return {}, ["No data available for analysis"]

    # Filter out upper limits for bias analysis of detected values?
    # The task asks for "retrieved water abundances". Upper limits are censored.
    # We will analyze the detected values (is_upper_limit == False) for mean/std.
    # We will also report counts of upper limits per instrument as a secondary metric.
    detected = merged[merged['is_upper_limit'] == False].copy()
    censored = merged[merged['is_upper_limit'] == True].copy()

    if detected.empty:
        logger.warning("No detected water abundances found to analyze for bias.")
        return {}, ["No detected values available for bias analysis"]

    detected['temp_bin'] = bin_temperature(detected['temperature'], temp_bins)

    instrument_bias_analysis = {}
    systematic_error_flags = []

    # Calculate global median for comparison
    global_median = detected['water_mixing_ratio'].median()
    logger.info(f"Global median water mixing ratio: {global_median:.4f}")

    # Group by instrument
    for instrument, group in detected.groupby('instrument'):
        instrument_stats = {
            'count': int(len(group)),
            'mean_water_abundance': float(group['water_mixing_ratio'].mean()),
            'std_water_abundance': float(group['water_mixing_ratio'].std()),
            'median_water_abundance': float(group['water_mixing_ratio'].median()),
            'temp_bin_breakdown': {}
        }

        # Breakdown by temperature bin
        for temp_bin, bin_group in group.groupby('temp_bin'):
            instrument_stats['temp_bin_breakdown'][temp_bin] = {
                'count': int(len(bin_group)),
                'mean': float(bin_group['water_mixing_ratio'].mean()) if not bin_group.empty else None,
                'std': float(bin_group['water_mixing_ratio'].std()) if len(bin_group) > 1 else None
            }

        # Check for systematic bias relative to global median
        # Using a simple threshold: if mean deviates > 0.5 dex from global median
        deviation = abs(instrument_stats['mean_water_abundance'] - global_median)
        if deviation > 0.5:
            flag_msg = f"Instrument {instrument} shows significant bias (deviation: {deviation:.2f} dex from global median)"
            systematic_error_flags.append(flag_msg)
            logger.warning(flag_msg)

        # Check for high variance (std > 1.0 dex)
        if instrument_stats['std_water_abundance'] > 1.0:
            flag_msg = f"Instrument {instrument} shows high variance in retrieved abundances (std: {instrument_stats['std_water_abundance']:.2f} dex)"
            systematic_error_flags.append(flag_msg)
            logger.warning(flag_msg)

        # Add censored count info
        censored_count = len(censored[censored['instrument'] == instrument])
        instrument_stats['upper_limit_count'] = censored_count

        instrument_bias_analysis[instrument] = instrument_stats

    return instrument_bias_analysis, systematic_error_flags

def generate_report_md(
    analysis_results: Dict[str, Any],
    flags: List[str],
    output_path: str
) -> None:
    """Generate the Markdown report for instrument calibration validation."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Instrument-Specific Calibration Validation Report",
        "",
        "This report addresses the requirement to identify systematic instrument biases",
        "by analyzing retrieved water abundances grouped by instrument and equilibrium temperature.",
        "",
        "## Summary",
        "",
        f"**Instruments Analyzed:** {len(analysis_results)}",
        f"**Systematic Error Flags:** {len(flags)}",
        "",
    ]

    if flags:
        lines.append("### Systematic Error Flags")
        lines.append("")
        for flag in flags:
            lines.append(f"- {flag}")
        lines.append("")

    lines.append("## Instrument Breakdown")
    lines.append("")

    for instrument, stats in analysis_results.items():
        lines.append(f"### {instrument}")
        lines.append("")
        lines.append(f"- **Total Detections:** {stats['count']}")
        lines.append(f"- **Upper Limits:** {stats['upper_limit_count']}")
        lines.append(f"- **Mean Water Abundance:** {stats['mean_water_abundance']:.4f}")
        lines.append(f"- **Std Deviation:** {stats['std_water_abundance']:.4f}")
        lines.append(f"- **Median Water Abundance:** {stats['median_water_abundance']:.4f}")
        lines.append("")
        lines.append("#### Temperature Bin Breakdown")
        lines.append("")
        lines.append("| Temp Bin | Count | Mean | Std |")
        lines.append("| :--- | :--- | :--- | :--- |")

        for temp_bin, bin_stats in stats['temp_bin_breakdown'].items():
            mean_val = f"{bin_stats['mean']:.4f}" if bin_stats['mean'] is not None else "N/A"
            std_val = f"{bin_stats['std']:.4f}" if bin_stats['std'] is not None else "N/A"
            lines.append(f"| {temp_bin} | {bin_stats['count']} | {mean_val} | {std_val} |")
        lines.append("")

    # Write to file
    with open(path, 'w') as f:
        f.write('\n'.join(lines))

    logger.info(f"Report written to {path}")

def main():
    """Main entry point for the instrument calibration validation task."""
    config = get_config()
    setup_logging()

    # Define paths based on project structure
    # T012 deliverable: data/processed/metadata.csv
    # T020 deliverable: data/processed/retrieval_results.csv
    metadata_path = Path(config['data_dir']) / 'processed' / 'metadata.csv'
    retrieval_path = Path(config['data_dir']) / 'processed' / 'retrieval_results.csv'
    output_path = Path(config['results_dir']) / 'instrument_calibration_report.md'

    if not metadata_path.exists():
        raise FileNotFoundError(f"Required metadata file missing: {metadata_path}. "
                                "Ensure T012 (save_metadata_csv) has been run.")
    if not retrieval_path.exists():
        raise FileNotFoundError(f"Required retrieval results file missing: {retrieval_path}. "
                                "Ensure T020 (save_retrieval_results) has been run.")

    try:
        logger.info("Starting Instrument Calibration Validation (T050)...")

        # Load data
        metadata_df = load_metadata(str(metadata_path))
        retrieval_df = load_retrieval_results(str(retrieval_path))

        # Analyze bias
        analysis_results, flags = analyze_instrument_bias(metadata_df, retrieval_df)

        # Generate report
        generate_report_md(analysis_results, flags, str(output_path))

        logger.info("Instrument Calibration Validation completed successfully.")

    except Exception as e:
        logger.error(f"Failed to complete Instrument Calibration Validation: {e}")
        raise

if __name__ == "__main__":
    main()
