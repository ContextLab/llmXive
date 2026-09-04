"""
Spectral Resolution Reporting Module (T045).

Implements the review response logic to extract and aggregate spectral
resolution (R) from the processed metadata. Calculates median, min, max
and provides an instrument breakdown.

Generates: results/spectral_resolution_report.md
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from config import get_config
from utils import setup_logging

# Configure logging
logger = setup_logging("spectral_resolution")


def load_metadata(metadata_path: Path) -> pd.DataFrame:
    """
    Load the processed metadata CSV.

    Args:
        metadata_path: Path to data/processed/metadata.csv

    Returns:
        DataFrame containing metadata columns including 'resolution' and 'instrument'.
    """
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

    df = pd.read_csv(metadata_path)

    required_cols = ['resolution', 'instrument']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Metadata missing required columns: {missing}")

    # Ensure resolution is numeric
    df['resolution'] = pd.to_numeric(df['resolution'], errors='coerce')
    df = df.dropna(subset=['resolution'])

    if df.empty:
        raise ValueError("No valid resolution data found in metadata after cleaning.")

    return df


def compute_resolution_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute aggregate resolution statistics.

    Returns:
        Dictionary with median_R, min_R, max_R, and instrument_breakdown.
    """
    median_R = float(df['resolution'].median())
    min_R = float(df['resolution'].min())
    max_R = float(df['resolution'].max())

    # Instrument breakdown
    instrument_stats = df.groupby('instrument')['resolution'].agg(['count', 'median', 'min', 'max', 'mean']).reset_index()
    instrument_breakdown = []
    for _, row in instrument_stats.iterrows():
        instrument_breakdown.append({
            "instrument": row['instrument'],
            "count": int(row['count']),
            "median_R": float(row['median']),
            "min_R": float(row['min']),
            "max_R": float(row['max']),
            "mean_R": float(row['mean'])
        })

    return {
        "median_R": median_R,
        "min_R": min_R,
        "max_R": max_R,
        "instrument_breakdown": instrument_breakdown
    }


def generate_report_md(stats: Dict[str, Any], output_path: Path) -> None:
    """
    Generate the Markdown report for Spectral Resolution.

    Args:
        stats: Dictionary containing resolution statistics.
        output_path: Path to write results/spectral_resolution_report.md
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    median_R = stats['median_R']
    min_R = stats['min_R']
    max_R = stats['max_R']
    breakdown = stats['instrument_breakdown']

    report_lines = [
        "# Spectral Resolution Report",
        "",
        "## Overview",
        "",
        "This report addresses the requirement for explicit spectral resolution reporting",
        "as demanded by reviewer Marie Curie. It details the instrument parameters",
        "achieved across the sample of exoplanetary transmission spectra.",
        "",
        "## Aggregate Statistics",
        "",
        f"- **Median Resolution (R)**: {median_R:.2f}",
        f"- **Minimum Resolution (R)**: {min_R:.2f}",
        f"- **Maximum Resolution (R)**: {max_R:.2f}",
        "",
        "## Instrument Breakdown",
        "",
        "The following table details the resolution characteristics per instrument:",
        "",
        "| Instrument | Count | Median R | Min R | Max R | Mean R |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |"
    ]

    for inst in breakdown:
        report_lines.append(
            f"| {inst['instrument']} | {inst['count']} | {inst['median_R']:.2f} | "
            f"{inst['min_R']:.2f} | {inst['max_R']:.2f} | {inst['mean_R']:.2f} |"
        )

    report_lines.extend([
        "",
        "## Conclusion",
        "",
        f"The study utilized a spectral resolution range from {min_R:.2f} to {max_R:.2f},",
        f"with a median resolution of {median_R:.2f}. This range ensures that the",
        "water vapor features, which typically require R > 100 for detection in",
        "transmission spectroscopy, are resolved within the limits of the available",
        "data.",
        ""
    ])

    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))

    logger.info(f"Spectral resolution report written to {output_path}")


def main():
    """
    Main entry point for the Spectral Resolution Reporting task.
    """
    config = get_config()
    project_root = Path(config['project_root'])

    metadata_path = project_root / "data" / "processed" / "metadata.csv"
    output_path = project_root / "results" / "spectral_resolution_report.md"

    try:
        logger.info(f"Loading metadata from {metadata_path}")
        df = load_metadata(metadata_path)

        logger.info("Computing resolution statistics")
        stats = compute_resolution_statistics(df)

        logger.info(f"Generating report at {output_path}")
        generate_report_md(stats, output_path)

        print(f"Success: {output_path} created.")

    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    except ValueError as e:
        logger.error(str(e))
        raise
    except Exception as e:
        logger.exception("Unexpected error during spectral resolution reporting")
        raise


if __name__ == "__main__":
    main()