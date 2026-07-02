import json
import csv
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Define log file paths relative to project root
# The project root is assumed to be the parent of the 'code' directory
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_LOGS_DIR = _PROJECT_ROOT / "logs"
_PAIRING_LOG_PATH = _LOGS_DIR / "data_pairing.json"
_FILTERING_LOG_PATH = _LOGS_DIR / "feature_filtering.csv"

# Ensure logs directory exists
_LOGS_DIR.mkdir(parents=True, exist_ok=True)


def _load_pairing_log() -> List[Dict[str, Any]]:
    """Load existing pairing log if it exists, otherwise return empty list."""
    if _PAIRING_LOG_PATH.exists():
        try:
            with open(_PAIRING_LOG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # If file is corrupted or unreadable, start fresh
            return []
    return []


def _save_pairing_log(records: List[Dict[str, Any]]) -> None:
    """Save pairing log records to JSON file."""
    with open(_PAIRING_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def log_data_pairing_mismatch(
    sample_id: str,
    expression_source: str,
    metabolite_source: str,
    reason: str = "no_sample_level_pair"
) -> None:
    """
    Log a single data pairing mismatch to the JSON log file.

    Args:
        sample_id: The identifier of the sample that failed to pair.
        expression_source: The source of the expression data (e.g., GEO accession).
        metabolite_source: The source of the metabolite data (e.g., Metabolomics Workbench ID).
        reason: The reason for the mismatch (default: "no_sample_level_pair").
    """
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "sample_id": sample_id,
        "expression_source": expression_source,
        "metabolite_source": metabolite_source,
        "reason": reason
    }

    current_records = _load_pairing_log()
    current_records.append(record)
    _save_pairing_log(current_records)


def log_data_pairing_mismatches_batch(
    mismatches: List[Dict[str, str]]
) -> None:
    """
    Log a batch of data pairing mismatches.

    Args:
        mismatches: List of dicts with keys: sample_id, expression_source,
                    metabolite_source, reason.
    """
    current_records = _load_pairing_log()
    for m in mismatches:
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "sample_id": m.get("sample_id", "unknown"),
            "expression_source": m.get("expression_source", "unknown"),
            "metabolite_source": m.get("metabolite_source", "unknown"),
            "reason": m.get("reason", "unknown")
        }
        current_records.append(record)
    _save_pairing_log(current_records)


def get_pairing_log_stats() -> Dict[str, Any]:
    """
    Get statistics about the current pairing log.

    Returns:
        Dict with total count and breakdown by reason.
    """
    records = _load_pairing_log()
    reasons = {}
    for r in records:
        reason = r.get("reason", "unknown")
        reasons[reason] = reasons.get(reason, 0) + 1

    return {
        "total_mismatches": len(records),
        "by_reason": reasons,
        "log_file_path": str(_PAIRING_LOG_PATH)
    }


def log_zero_variance_feature(
    gene_id: str,
    variance: float,
    reason: str = "zero_variance"
) -> None:
    """
    Log a single zero-variance feature to the CSV log file.

    Args:
        gene_id: The identifier of the gene with zero variance.
        variance: The calculated variance value.
        reason: The reason for filtering (default: "zero_variance").
    """
    # Check if file exists to determine if header is needed
    file_exists = _FILTERING_LOG_PATH.exists()

    with open(_FILTERING_LOG_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["gene_id", "variance", "reason", "timestamp"])

        writer.writerow([
            gene_id,
            f"{variance:.10e}",
            reason,
            datetime.utcnow().isoformat()
        ])


def log_zero_variance_features_batch(
    features: List[Dict[str, Any]]
) -> None:
    """
    Log a batch of zero-variance features.

    Args:
        features: List of dicts with keys: gene_id, variance, reason.
    """
    file_exists = _FILTERING_LOG_PATH.exists()

    with open(_FILTERING_LOG_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["gene_id", "variance", "reason", "timestamp"])

        for feat in features:
            writer.writerow([
                feat.get("gene_id", "unknown"),
                f"{feat.get('variance', 0.0):.10e}",
                feat.get("reason", "zero_variance"),
                datetime.utcnow().isoformat()
            ])


def get_filtering_log_stats() -> Dict[str, Any]:
    """
    Get statistics about the current filtering log.

    Returns:
        Dict with total count and breakdown by reason.
    """
    if not _FILTERING_LOG_PATH.exists():
        return {
            "total_filtered": 0,
            "by_reason": {},
            "log_file_path": str(_FILTERING_LOG_PATH)
        }

    total = 0
    reasons = {}

    with open(_FILTERING_LOG_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            reason = row.get("reason", "unknown")
            reasons[reason] = reasons.get(reason, 0) + 1

    return {
        "total_filtered": total,
        "by_reason": reasons,
        "log_file_path": str(_FILTERING_LOG_PATH)
    }
