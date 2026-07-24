"""
Logging utilities for the plant defense compound prediction pipeline.

This module provides functions to log data pairing mismatches and zero-variance
feature filtering events to specific log files as required by spec.md edge cases.

Log Files:
- logs/data_pairing.json: Stores sample-level pairing mismatches.
- logs/feature_filtering.csv: Stores zero-variance gene filtering events.
"""

import json
import csv
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Define project root and log paths relative to the project structure
# We assume this code runs from the project root or the code directory
# The paths must be absolute or relative to the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
PAIRING_LOG_PATH = LOGS_DIR / "data_pairing.json"
FILTERING_LOG_PATH = LOGS_DIR / "feature_filtering.csv"

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def _ensure_pairing_log_exists() -> List[Dict[str, Any]]:
    """Load existing pairing log or initialize a new list."""
    if PAIRING_LOG_PATH.exists():
        try:
            with open(PAIRING_LOG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, list):
                    # If file exists but is not a list, overwrite with empty list
                    return []
                return data
        except (json.JSONDecodeError, IOError):
            return []
    return []


def _save_pairing_log(data: List[Dict[str, Any]]) -> None:
    """Save the pairing log to disk."""
    with open(PAIRING_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def log_data_pairing_mismatch(
    sample_id: str,
    expression_source: str,
    metabolite_source: str,
    reason: str = "no_sample_level_pair"
) -> None:
    """
    Log a single data pairing mismatch to logs/data_pairing.json.

    Args:
        sample_id: The identifier of the sample that failed to pair.
        expression_source: The source dataset/file for the expression data.
        metabolite_source: The source dataset/file for the metabolite data.
        reason: The reason for the mismatch (default: "no_sample_level_pair").
    """
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "sample_id": sample_id,
        "expression_source": expression_source,
        "metabolite_source": metabolite_source,
        "reason": reason
    }

    current_log = _ensure_pairing_log_exists()
    current_log.append(entry)
    _save_pairing_log(current_log)


def log_data_pairing_mismatches_batch(
    mismatches: List[Dict[str, str]]
) -> None:
    """
    Log multiple data pairing mismatches to logs/data_pairing.json.

    Args:
        mismatches: A list of dictionaries, each containing keys:
                    sample_id, expression_source, metabolite_source, reason.
    """
    current_log = _ensure_pairing_log_exists()
    timestamp = datetime.utcnow().isoformat()

    for mismatch in mismatches:
        entry = {
            "timestamp": timestamp,
            "sample_id": mismatch.get("sample_id", "unknown"),
            "expression_source": mismatch.get("expression_source", "unknown"),
            "metabolite_source": mismatch.get("metabolite_source", "unknown"),
            "reason": mismatch.get("reason", "no_sample_level_pair")
        }
        current_log.append(entry)

    _save_pairing_log(current_log)


def get_pairing_log_stats() -> Dict[str, Any]:
    """
    Retrieve statistics about the current pairing log.

    Returns:
        A dictionary with count of mismatches and breakdown by reason.
    """
    current_log = _ensure_pairing_log_exists()
    reasons = {}
    for entry in current_log:
        reason = entry.get("reason", "unknown")
        reasons[reason] = reasons.get(reason, 0) + 1

    return {
        "total_mismatches": len(current_log),
        "by_reason": reasons,
        "log_path": str(PAIRING_LOG_PATH)
    }


def _ensure_filtering_log_exists() -> None:
    """Initialize the filtering CSV if it doesn't exist with headers."""
    if not FILTERING_LOG_PATH.exists():
        with open(FILTERING_LOG_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "gene_id", "variance", "reason"])


def log_zero_variance_feature(
    gene_id: str,
    variance: float,
    reason: str = "zero_variance"
) -> None:
    """
    Log a single zero-variance gene to logs/feature_filtering.csv.

    Args:
        gene_id: The identifier of the gene with zero variance.
        variance: The calculated variance value.
        reason: The reason for filtering (default: "zero_variance").
    """
    _ensure_filtering_log_exists()
    timestamp = datetime.utcnow().isoformat()

    with open(FILTERING_LOG_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, gene_id, f"{variance:.2e}", reason])


def log_zero_variance_features_batch(
    features: List[Dict[str, Any]]
) -> None:
    """
    Log multiple zero-variance genes to logs/feature_filtering.csv.

    Args:
        features: A list of dictionaries, each containing keys:
                  gene_id, variance, reason.
    """
    _ensure_filtering_log_exists()
    timestamp = datetime.utcnow().isoformat()

    with open(FILTERING_LOG_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for feature in features:
            writer.writerow([
                timestamp,
                feature.get("gene_id", "unknown"),
                f"{feature.get('variance', 0):.2e}",
                feature.get("reason", "zero_variance")
            ])


def get_filtering_log_stats() -> Dict[str, Any]:
    """
    Retrieve statistics about the current filtering log.

    Returns:
        A dictionary with count of filtered features and breakdown by reason.
    """
    if not FILTERING_LOG_PATH.exists():
        return {
            "total_filtered": 0,
            "by_reason": {},
            "log_path": str(FILTERING_LOG_PATH)
        }

    filtered_count = 0
    reasons = {}

    with open(FILTERING_LOG_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            filtered_count += 1
            reason = row.get("reason", "unknown")
            reasons[reason] = reasons.get(reason, 0) + 1

    return {
        "total_filtered": filtered_count,
        "by_reason": reasons,
        "log_path": str(FILTERING_LOG_PATH)
    }


def main():
    """
    Main function to demonstrate logging functionality.
    This is useful for testing the logging utilities independently.
    """
    print("Testing logging utilities...")

    # Test pairing log
    log_data_pairing_mismatch(
        sample_id="SAMPLE_001",
        expression_source="GEO_GSM123456",
        metabolite_source="MW_EXP789",
        reason="no_sample_level_pair"
    )
    log_data_pairing_mismatch(
        sample_id="SAMPLE_002",
        expression_source="GEO_GSM123457",
        metabolite_source="MW_EXP789",
        reason="missing_metabolite_id"
    )
    log_data_pairing_mismatches_batch([
        {
            "sample_id": "SAMPLE_003",
            "expression_source": "GEO_GSM123458",
            "metabolite_source": "MW_EXP789",
            "reason": "inconsistent_metadata"
        }
    ])

    print(f"Pairing log stats: {get_pairing_log_stats()}")

    # Test filtering log
    log_zero_variance_feature(
        gene_id="AT1G01010",
        variance=0.0,
        reason="zero_variance"
    )
    log_zero_variance_features_batch([
        {
            "gene_id": "AT1G01020",
            "variance": 1e-15,
            "reason": "zero_variance"
        },
        {
            "gene_id": "AT1G01030",
            "variance": 5e-11,
            "reason": "near_zero_variance"
        }
    ])

    print(f"Filtering log stats: {get_filtering_log_stats()}")
    print("Logging utilities test completed successfully.")


if __name__ == "__main__":
    main()