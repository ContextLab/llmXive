"""
Instrument-Specific Calibration Validation (T050).

Per Marie Curie's demand for "what is the instrument?", this module:
1. Parses metadata.csv to group results by instrument (HST, Spitzer, etc.).
2. Bins planets by equilibrium temperature.
3. Calculates mean and standard deviation of retrieved water abundances per instrument/temperature bin.
4. Detects systematic biases (instrument-specific offsets) and flags them.
5. Generates a comprehensive markdown report: results/instrument_calibration_report.md.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from utils import setup_logging, PipelineError
from config import get_config

logger = logging.getLogger(__name__)

def load_metadata(filepath: Path) -> pd.DataFrame:
    """Load metadata CSV."""
    if not filepath.exists():
        raise PipelineError(f"Metadata file not found: {filepath}")
    df = pd.read_csv(filepath)
    required_cols = ['planet_name', 'temperature', 'instrument']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise PipelineError(f"Missing required columns in metadata: {missing}")
    return df

def load_retrieval_results(filepath: Path) -> pd.DataFrame:
    """Load retrieval results CSV."""
    if not filepath.exists():
        raise PipelineError(f"Retrieval results file not found: {filepath}")
    df = pd.read_csv(filepath)
    required_cols = ['planet_name', 'water_mixing_ratio', 'is_upper_limit']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise PipelineError(f"Missing required columns in retrieval results: {missing}")
    return df

def bin_temperature(temp: float, bin_width: float = 200.0) -> float:
    """Bin equilibrium temperature to the nearest bin_width."""
    if pd.isna(temp):
        return np.nan
    return round(temp / bin_width) * bin_width

def analyze_instrument_bias(
    metadata_df: pd.DataFrame,
    retrieval_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Group by instrument and temperature bins, calculate stats, and detect biases.

    Returns a dictionary with:
    - instrument_bias_analysis: list of bin stats
    - systematic_error_flags: list of flagged instruments
    """
    # Merge data
    merged = pd.merge(
        metadata_df[['planet_name', 'temperature', 'instrument']],
        retrieval_df[['planet_name', 'water_mixing_ratio', 'is_upper_limit']],
        on='planet_name',
        how='inner'
    )

    if merged.empty:
        raise PipelineError("No matching data found between metadata and retrieval results.")

    # Create temperature bins
    merged['temp_bin'] = merged['temperature'].apply(bin_temperature)

    # Filter out upper limits for bias calculation (we want measured values)
    # Note: We could include upper limits with special handling, but for bias detection
    # of the instrument's central tendency, measured values are more direct.
    measured = merged[merged['is_upper_limit'] == False].copy()

    if measured.empty:
        logger.warning("No non-upper-limit measurements found for bias analysis.")
        return {
            'instrument_bias_analysis': [],
            'systematic_error_flags': [],
            'note': 'No measured (non-upper-limit) data available for bias analysis.'
        }

    # Group by instrument and temperature bin
    groups = measured.groupby(['instrument', 'temp_bin'])

    analysis_results = []
    instrument_stats = {}

    for (instrument, temp_bin), group in groups:
        if len(group) < 2:
            # Need at least 2 points to calculate meaningful std dev
            continue

        mean_val = group['water_mixing_ratio'].mean()
        std_val = group['water_mixing_ratio'].std()
        count = len(group)
        median_val = group['water_mixing_ratio'].median()
        min_val = group['water_mixing_ratio'].min()
        max_val = group['water_mixing_ratio'].max()

        entry = {
            'instrument': instrument,
            'temperature_bin_center': float(temp_bin),
            'count': int(count),
            'mean_log10_water_mixing_ratio': float(mean_val),
            'std_log10_water_mixing_ratio': float(std_val),
            'median_log10_water_mixing_ratio': float(median_val),
            'min_log10_water_mixing_ratio': float(min_val),
            'max_log10_water_mixing_ratio': float(max_val)
        }
        analysis_results.append(entry)

        # Aggregate per instrument for global bias check
        if instrument not in instrument_stats:
            instrument_stats[instrument] = []
        instrument_stats[instrument].append(entry['mean_log10_water_mixing_ratio'])

    # Detect systematic biases:
    # If an instrument's mean values in a specific temperature range deviate significantly
    # from the global mean for that range, flag it.
    systematic_flags = []
    global_means = {}

    # Calculate global mean per temp bin (across all instruments)
    global_grouped = measured.groupby('temp_bin')['water_mixing_ratio'].mean()

    for entry in analysis_results:
        instrument = entry['instrument']
        temp_bin = entry['temperature_bin_center']
        mean_val = entry['mean_log10_water_mixing_ratio']

        if temp_bin in global_grouped:
            global_mean = global_grouped[temp_bin]
            deviation = abs(mean_val - global_mean)
            # Threshold: if deviation > 0.5 dex (factor of ~3), flag as potential bias
            # This is a heuristic based on typical exoplanet atmosphere uncertainties
            if deviation > 0.5:
                flag_entry = {
                    'instrument': instrument,
                    'temperature_bin': float(temp_bin),
                    'instrument_mean': float(mean_val),
                    'global_mean': float(global_mean),
                    'deviation_dex': float(deviation),
                    'reason': f"Instrument {instrument} shows {deviation:.2f} dex deviation from global mean at T~{temp_bin}K"
                }
                systematic_flags.append(flag_entry)

    return {
        'instrument_bias_analysis': analysis_results,
        'systematic_error_flags': systematic_flags
    }

def generate_report_md(analysis_data: Dict[str, Any], output_path: Path) -> None:
    """Generate the markdown report."""
    lines = []
    lines.append("# Instrument-Specific Calibration Validation Report")
    lines.append("")
    lines.append("## Overview")
    lines.append("This report addresses the requirement for instrument-specific calibration validation.")
    lines.append("It analyzes retrieved water abundances grouped by instrument and equilibrium temperature bins")
    lines.append("to detect systematic biases or calibration offsets.")
    lines.append("")

    # Summary
    analysis_list = analysis_data.get('instrument_bias_analysis', [])
    flags_list = analysis_data.get('systematic_error_flags', [])

    lines.append(f"### Summary")
    lines.append(f"- **Total Instrument-Temperature Bins Analyzed**: {len(analysis_list)}")
    lines.append(f"- **Systematic Bias Flags Raised**: {len(flags_list)}")
    if 'note' in analysis_data:
        lines.append(f"- **Note**: {analysis_data['note']}")
    lines.append("")

    # Instrument Breakdown
    lines.append("## Instrument Breakdown")
    lines.append("")
    lines.append("| Instrument | Temp Bin (K) | Count | Mean Log10(H2O) | Std Dev | Min | Max |")
    lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")

    for entry in sorted(analysis_list, key=lambda x: (x['instrument'], x['temperature_bin_center'])):
        lines.append(
            f"| {entry['instrument']} | {entry['temperature_bin_center']:.0f} | "
            f"{entry['count']} | {entry['mean_log10_water_mixing_ratio']:.3f} | "
            f"{entry['std_log10_water_mixing_ratio']:.3f} | "
            f"{entry['min_log10_water_mixing_ratio']:.3f} | "
            f"{entry['max_log10_water_mixing_ratio']:.3f} |"
        )
    lines.append("")

    # Systematic Errors
    lines.append("## Systematic Error Flags")
    lines.append("")
    if not flags_list:
        lines.append("No significant systematic biases were detected at the >0.5 dex threshold.")
    else:
        lines.append("The following instruments show significant deviations from the global mean in specific temperature bins:")
        lines.append("")
        for flag in flags_list:
            lines.append(f"- **{flag['instrument']}** at T~{flag['temperature_bin']:.0f}K:")
            lines.append(f"  - Instrument Mean: {flag['instrument_mean']:.3f}")
            lines.append(f"  - Global Mean: {flag['global_mean']:.3f}")
            lines.append(f"  - Deviation: {flag['deviation_dex']:.3f} dex")
            lines.append(f"  - Reason: {flag['reason']}")
            lines.append("")

    # Conclusion
    lines.append("## Conclusion")
    lines.append("This analysis provides evidence for (or against) instrument-specific calibration biases.")
    lines.append("Significant deviations suggest that data from specific instruments may require")
    lines.append("additional calibration correction before being combined in a global analysis.")
    lines.append("")

    content = "\n".join(lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)
    logger.info(f"Report generated: {output_path}")

def main():
    """Main entry point."""
    config = get_config()
    base_path = Path(config['project_root'])
    metadata_path = base_path / 'data' / 'processed' / 'metadata.csv'
    retrieval_path = base_path / 'data' / 'processed' / 'retrieval_results.csv'
    output_path = base_path / 'results' / 'instrument_calibration_report.md'

    setup_logging()
    logger.info("Starting Instrument Calibration Validation (T050)")

    try:
        logger.info(f"Loading metadata from {metadata_path}")
        metadata_df = load_metadata(metadata_path)
        logger.info(f"Loaded {len(metadata_df)} rows from metadata")

        logger.info(f"Loading retrieval results from {retrieval_path}")
        retrieval_df = load_retrieval_results(retrieval_path)
        logger.info(f"Loaded {len(retrieval_df)} rows from retrieval results")

        logger.info("Analyzing instrument bias...")
        analysis_data = analyze_instrument_bias(metadata_df, retrieval_df)

        logger.info(f"Generating report at {output_path}")
        generate_report_md(analysis_data, output_path)

        logger.info("Instrument Calibration Validation completed successfully.")
        return 0

    except PipelineError as e:
        logger.error(f"Pipeline error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())
