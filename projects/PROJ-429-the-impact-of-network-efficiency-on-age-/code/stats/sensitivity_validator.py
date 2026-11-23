import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any

from config import ensure_dirs, get_config_summary

logger = logging.getLogger(__name__)

def load_csv_if_exists(file_path: Path) -> pd.DataFrame:
    """Load a CSV file if it exists, otherwise return an empty DataFrame."""
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}. Returning empty DataFrame.")
        return pd.DataFrame()
    try:
        df = pd.read_csv(file_path)
        if df.empty:
            logger.warning(f"File {file_path} exists but is empty.")
        return df
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return pd.DataFrame()

def calculate_overall_stability(density_stable: bool, artifact_stable: bool) -> bool:
    """
    Determine overall stability.
    Returns True only if both density and artifact stability are True.
    """
    return density_stable and artifact_stable

def validate_density_stability(df: pd.DataFrame) -> bool:
    """
    Validate density stability from T018a output.
    Checks if 'is_stable' is True for all rows or majority of rows.
    Returns True if stable, False otherwise.
    """
    if df.empty:
        logger.warning("Density stability dataframe is empty. Marking as unstable.")
        return False

    if 'is_stable' not in df.columns:
        logger.error("Column 'is_stable' missing in density stability data.")
        return False

    # Check if all rows are stable
    all_stable = df['is_stable'].all()
    # Check if majority are stable (optional, but stricter is better for validation)
    majority_stable = df['is_stable'].mean() > 0.8

    logger.info(f"Density stability check: all_stable={all_stable}, majority_stable={majority_stable}")
    return all_stable

def validate_artifact_stability(df: pd.DataFrame) -> bool:
    """
    Validate artifact stability from T018b output.
    Checks if 'is_stable' is True for all rows or majority of rows.
    Returns True if stable, False otherwise.
    """
    if df.empty:
        logger.warning("Artifact stability dataframe is empty. Marking as unstable.")
        return False

    if 'is_stable' not in df.columns:
        logger.error("Column 'is_stable' missing in artifact stability data.")
        return False

    all_stable = df['is_stable'].all()
    majority_stable = df['is_stable'].mean() > 0.8

    logger.info(f"Artifact stability check: all_stable={all_stable}, majority_stable={majority_stable}")
    return all_stable

def main():
    """
    Main function to aggregate sensitivity analysis results and generate a summary.
    Reads T018a and T018b outputs, validates them, and writes T018c summary.
    """
    config = get_config_summary()
    ensure_dirs()

    # Define paths based on project structure
    base_path = Path(config['paths']['results'])
    density_report_path = base_path / 'sensitivity_density_report.csv'
    artifact_report_path = base_path / 'sensitivity_artifact_report.csv'
    summary_output_path = base_path / 'sensitivity_summary.json'

    logger.info(f"Starting sensitivity validation (T018c).")
    logger.info(f"Looking for density report at: {density_report_path}")
    logger.info(f"Looking for artifact report at: {artifact_report_path}")

    # Load upstream data
    density_df = load_csv_if_exists(density_report_path)
    artifact_df = load_csv_if_exists(artifact_report_path)

    # Validate stability
    density_stable = validate_density_stability(density_df)
    artifact_stable = validate_artifact_stability(artifact_df)

    # Determine overall status
    overall_stable = calculate_overall_stability(density_stable, artifact_stable)

    # Construct summary
    summary = {
        "density_stable": density_stable,
        "artifact_stable": artifact_stable,
        "overall_stable": overall_stable,
        "status": "COMPLETE",
        "reason": ""
    }

    # Handle missing data scenarios
    if density_df.empty and artifact_df.empty:
        summary["status"] = "PARTIAL"
        summary["reason"] = "Missing upstream sensitivity data (both density and artifact reports missing)."
    elif density_df.empty:
        summary["status"] = "PARTIAL"
        summary["reason"] = "Missing upstream sensitivity data (density report missing)."
    elif artifact_df.empty:
        summary["status"] = "PARTIAL"
        summary["reason"] = "Missing upstream sensitivity data (artifact report missing)."
    else:
        # Both exist, so status is complete, reason is empty or specific stability notes
        if not overall_stable:
            summary["reason"] = "Stability criteria not met for one or more parameters."
        else:
            summary["reason"] = "All sensitivity analyses passed stability checks."

    logger.info(f"Generated summary: {summary}")

    # Ensure output directory exists
    ensure_dirs()

    # Write summary to JSON
    with open(summary_output_path, 'w') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Sensitivity summary written to: {summary_output_path}")
    return 0

if __name__ == '__main__':
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    sys.exit(main())
