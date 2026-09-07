"""
Noise Stability Analysis Module (Task T047).

Implements Calibration & Noise Stability Analysis per Marie Curie's concern
about "quantity of photons and stability of the detector".

Logic:
1. Load metadata from data/processed/metadata.csv.
2. Compute Coefficient of Variation (CV) for SNR across all spectra.
3. Group by instrument and calculate variance/CV for each.
4. Flag instruments with CV > 0.20 (20%) as potential confounding factors.
5. Generate a Markdown report at results/noise_stability_report.md.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from config import get_config
from utils import setup_logging

logger = logging.getLogger(__name__)

def load_metadata(config: Dict[str, Any]) -> pd.DataFrame:
    """
    Load the processed metadata CSV.
    
    Args:
        config: Configuration dictionary containing paths.
        
    Returns:
        DataFrame with metadata columns including 'snr' and 'instrument'.
        
    Raises:
        FileNotFoundError: If metadata.csv does not exist.
        ValueError: If required columns are missing.
    """
    metadata_path = Path(config["paths"]["processed"]) / "metadata.csv"
    
    if not metadata_path.exists():
        raise FileNotFoundError(
            f"Required metadata file not found: {metadata_path}. "
            "Ensure T012 (save_metadata_csv) has been executed successfully."
        )
    
    df = pd.read_csv(metadata_path)
    
    required_cols = ["snr", "instrument"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Metadata file missing required columns: {missing_cols}. "
            f"Found: {list(df.columns)}"
        )
    
    # Ensure SNR is numeric
    df["snr"] = pd.to_numeric(df["snr"], errors="coerce")
    df = df.dropna(subset=["snr"])
    
    if df.empty:
        raise ValueError("No valid SNR data found in metadata file.")
        
    logger.info(f"Loaded {len(df)} records from {metadata_path}")
    return df

def calculate_snr_cv(df: pd.DataFrame) -> float:
    """
    Calculate the Coefficient of Variation (CV) for the SNR column.
    
    CV = Standard Deviation / Mean.
    
    Args:
        df: DataFrame containing 'snr' column.
        
    Returns:
        float: The CV of the SNR.
    """
    snr_mean = df["snr"].mean()
    snr_std = df["snr"].std()
    
    if snr_mean == 0:
        logger.warning("Mean SNR is zero; CV is undefined. Returning 0.0.")
        return 0.0
        
    cv = snr_std / snr_mean
    logger.info(f"Global SNR CV calculated: {cv:.4f}")
    return float(cv)

def analyze_instrument_stability(df: pd.DataFrame, threshold: float = 0.20) -> Dict[str, Any]:
    """
    Analyze SNR stability per instrument and flag high variance.
    
    Args:
        df: DataFrame with 'snr' and 'instrument' columns.
        threshold: CV threshold (default 0.20) to flag an instrument.
        
    Returns:
        Dictionary containing:
            - instrument_stats: Dict of {instrument: {mean, std, cv, count}}
            - flagged_instruments: List of instrument names with CV > threshold
            - global_cv: Global SNR CV
    """
    instrument_stats = {}
    flagged_instruments = []
    
    instruments = df["instrument"].unique()
    
    for inst in instruments:
        subset = df[df["instrument"] == inst]
        mean_val = subset["snr"].mean()
        std_val = subset["snr"].std()
        count = len(subset)
        
        if mean_val == 0:
            cv = 0.0
        else:
            cv = std_val / mean_val
        
        instrument_stats[inst] = {
            "mean_snr": float(mean_val),
            "std_snr": float(std_val),
            "cv": float(cv),
            "count": int(count)
        }
        
        if cv > threshold:
            flagged_instruments.append(inst)
            logger.warning(f"Instrument '{inst}' flagged for high SNR variance (CV={cv:.2%} > {threshold:.2%})")
        
    global_cv = calculate_snr_cv(df)
    
    return {
        "instrument_stats": instrument_stats,
        "flagged_instruments": flagged_instruments,
        "global_cv": global_cv
    }

def generate_report_md(analysis_results: Dict[str, Any], output_path: Path) -> None:
    """
    Generate the Markdown report for noise stability analysis.
    
    Args:
        analysis_results: Dictionary from analyze_instrument_stability.
        output_path: Path to write the .md file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    global_cv = analysis_results["global_cv"]
    flagged = analysis_results["flagged_instruments"]
    stats = analysis_results["instrument_stats"]
    
    report_lines = [
        "# Calibration & Noise Stability Analysis",
        "",
        "## Overview",
        "This report addresses the reviewer concern regarding the stability of the detector",
        "and the quantity of photons (SNR) across the sample. We compute the Coefficient of",
        "Variation (CV) for the Signal-to-Noise Ratio to identify instruments with high variance.",
        "",
        f"**Global SNR Coefficient of Variation (CV):** {global_cv:.4f} ({global_cv:.2%})",
        "",
        "## Instrument Stability Flags",
        "",
    ]
    
    if flagged:
        report_lines.append(
            f"The following instruments exhibit high SNR variance (CV > 20%), "
            f"indicating potential confounding factors in the analysis:"
        )
        report_lines.append("")
        for inst in flagged:
            report_lines.append(f"- **{inst}**")
        report_lines.append("")
    else:
        report_lines.append("No instruments exceeded the 20% CV threshold for high variance.")
        report_lines.append("")
        
    report_lines.extend([
        "## Detailed Instrument Statistics",
        "",
        "| Instrument | Mean SNR | Std SNR | CV | Count |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ])
    
    for inst, data in stats.items():
        report_lines.append(
            f"| {inst} | {data['mean_snr']:.2f} | {data['std_snr']:.2f} | "
            f"{data['cv']:.2%} | {data['count']} |"
        )
        
    report_lines.extend([
        "",
        "## Methodology",
        "",
        "- **Metric:** Coefficient of Variation (CV) = Standard Deviation / Mean.",
        "- **Threshold:** Instruments with CV > 0.20 (20%) are flagged.",
        "- **Data Source:** `data/processed/metadata.csv` (SNR column).",
        "- **Citation:** Stability analysis methodology adapted from standard spectroscopic calibration practices.",
    ])
    
    content = "\n".join(report_lines)
    output_path.write_text(content)
    logger.info(f"Generated noise stability report: {output_path}")

def main():
    """Main entry point for T047."""
    config = get_config()
    log_path = Path(config["paths"]["logs"]) / "noise_stability.log"
    setup_logging(log_file=log_path, level=logging.INFO)
    
    logger.info("Starting Noise Stability Analysis (T047)")
    
    try:
        # Load data
        df = load_metadata(config)
        
        # Analyze
        results = analyze_instrument_stability(df)
        
        # Generate report
        report_path = Path(config["paths"]["results"]) / "noise_stability_report.md"
        generate_report_md(results, report_path)
        
        logger.info("Noise Stability Analysis completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}")
        raise

if __name__ == "__main__":
    main()
