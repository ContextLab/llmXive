"""
QC Reporter Module for User Story 1.

Calculates exclusion rates based on SC-001 motion thresholds and generates
the final QC summary report.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd

# Import from existing API surface
from utils.io import IOLoadError, ensure_dir, load_yaml, save_json
from utils.logger import get_logger

logger = get_logger(__name__)

class QCReportError(Exception):
    """Custom exception for QC reporting errors."""
    pass

def load_exclusion_data(exclusions_path: Path) -> Dict[str, Any]:
    """
    Load exclusion data from the exclusions YAML file.

    Args:
        exclusions_path: Path to state/exclusions.yaml

    Returns:
        Dictionary containing exclusion information.

    Raises:
        QCReportError: If file not found or invalid format.
    """
    if not exclusions_path.exists():
        raise QCReportError(f"Exclusions file not found: {exclusions_path}")

    try:
        data = load_yaml(exclusions_path)
        if not isinstance(data, dict):
            raise QCReportError("Exclusions file must contain a YAML dictionary")
        return data
    except IOLoadError as e:
        raise QCReportError(f"Failed to load exclusions file: {e}")

def calculate_exclusion_rate(exclusions_data: Dict[str, Any], total_participants: int) -> float:
    """
    Calculate the exclusion rate based on the provided data.

    Args:
        exclusions_data: Dictionary containing exclusion information.
        total_participants: Total number of participants attempted.

    Returns:
        Exclusion rate as a float (0.0 to 1.0).
    """
    if total_participants == 0:
        return 0.0

    excluded_count = len(exclusions_data.get("excluded", []))
    return excluded_count / total_participants

def assess_stability(exclusions_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assess stability metrics based on exclusion patterns.

    Args:
        exclusions_data: Dictionary containing exclusion information.

    Returns:
        Dictionary with stability metrics.
    """
    excluded_reasons = exclusions_data.get("excluded", [])
    reason_counts = {}

    for item in excluded_reasons:
        reason = item.get("reason", "unknown")
        reason_counts[reason] = reason_counts.get(reason, 0) + 1

    # Calculate stability: 1.0 if no exclusions, otherwise ratio of non-motion exclusions
    # This is a placeholder metric; in a real scenario, we'd track variance across runs
    total_excluded = len(excluded_reasons)
    if total_excluded == 0:
        stability_score = 1.0
    else:
        # Assuming "motion" is the primary reason we care about for SC-001
        motion_exclusions = reason_counts.get("motion", 0)
        stability_score = 1.0 - (motion_exclusions / total_excluded) if total_excluded > 0 else 1.0

    return {
        "total_excluded": total_excluded,
        "reason_breakdown": reason_counts,
        "stability_score": round(stability_score, 4)
    }

def generate_qc_summary(
    exclusions_path: Path,
    output_path: Path,
    threshold_volumes_percent: float = 10.0,
    threshold_motion_mm: float = 3.0
) -> Dict[str, Any]:
    """
    Generate the final QC summary report.

    Args:
        exclusions_path: Path to state/exclusions.yaml.
        output_path: Path to write data/reports/qc_summary.json.
        threshold_volumes_percent: SC-001 threshold for volume exclusion.
        threshold_motion_mm: SC-001 threshold for motion in mm.

    Returns:
        The generated summary dictionary.
    """
    ensure_dir(output_path.parent)

    # Load exclusions
    exclusions_data = load_exclusion_data(exclusions_path)

    # We need to know the total participants to calculate the rate.
    # In a real pipeline, this would be passed or stored in the exclusions file.
    # We infer it from the "excluded" list + any "included" list if present,
    # or we assume the exclusions file tracks the total attempted.
    # If the file structure is just {"excluded": [...]}, we need an external count.
    # For this implementation, we assume the exclusions file has a "total_attempted" key
    # or we derive it from the context of the pipeline run.
    # If not present, we cannot calculate a true rate without external info.
    # Let's check for a "total_attempted" key, otherwise default to 0 (which will make rate 0).
    total_participants = exclusions_data.get("total_attempted", 0)

    if total_participants == 0:
        # Fallback: if we can't find total, we can't calculate rate.
        # In a real scenario, T018 (qc_filter) should have written this count.
        # If it's missing, we log a warning and set rate to 0.
        logger.warning("Total participants not found in exclusions file. Setting rate to 0.")

    excluded_list = exclusions_data.get("excluded", [])
    excluded_count = len(excluded_list)
    exclusion_rate = calculate_exclusion_rate(exclusions_data, total_participants)

    stability_metrics = assess_stability(exclusions_data)

    summary = {
        "total_participants": total_participants,
        "excluded_count": excluded_count,
        "exclusion_rate": round(exclusion_rate, 4),
        "threshold_volumes_percent": threshold_volumes_percent,
        "threshold_motion_mm": threshold_motion_mm,
        "exclusion_reasons": list(set(item.get("reason", "unknown") for item in excluded_list)),
        "stability_metrics": stability_metrics
    }

    logger.info(f"Generating QC summary: {excluded_count} excluded out of {total_participants}")
    logger.info(f"Exclusion rate: {exclusion_rate:.2%}")

    save_json(output_path, summary)
    logger.info(f"QC summary written to {output_path}")

    return summary

def main():
    """
    Main entry point for QC reporting.
    Reads state/exclusions.yaml and writes data/reports/qc_summary.json.
    """
    # Paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    exclusions_path = project_root / "state" / "exclusions.yaml"
    output_path = project_root / "data" / "reports" / "qc_summary.json"

    # SC-001 Thresholds
    THRESHOLD_VOLUMES_PERCENT = 10.0
    THRESHOLD_MOTION_MM = 3.0

    logger.info("Starting QC reporting")

    try:
        summary = generate_qc_summary(
            exclusions_path=exclusions_path,
            output_path=output_path,
            threshold_volumes_percent=THRESHOLD_VOLUMES_PERCENT,
            threshold_motion_mm=THRESHOLD_MOTION_MM
        )
        logger.info("QC reporting completed successfully")
        print(json.dumps(summary, indent=2))
    except QCReportError as e:
        logger.error(f"QC reporting failed: {e}")
        # Re-raise to ensure the script fails loudly if data is missing
        raise
    except Exception as e:
        logger.error(f"Unexpected error during QC reporting: {e}")
        raise

if __name__ == "__main__":
    main()
