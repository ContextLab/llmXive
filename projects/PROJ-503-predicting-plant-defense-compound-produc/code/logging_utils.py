"""
logging_utils.py

Utility functions for logging data pairing mismatches and feature filtering events.
This module provides functions to write to:
- logs/data_pairing.json (on mismatch)
- logs/feature_filtering.csv (on zero-variance filter)
"""
import json
import csv
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Define project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
DATA_PAIRING_LOG = LOGS_DIR / "data_pairing.json"
FEATURE_FILTERING_LOG = LOGS_DIR / "feature_filtering.csv"

def _ensure_log_dirs():
    """Ensure the logs directory exists."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

def log_data_pairing_mismatch(
    sample_id: str,
    expression_source: str,
    metabolite_source: str,
    reason: str = "no_sample_level_pair"
) -> None:
    """
    Log a single data pairing mismatch to logs/data_pairing.json.

    Args:
        sample_id: The biological sample identifier that failed to pair.
        expression_source: Source dataset/file for expression data.
        metabolite_source: Source dataset/file for metabolite data.
        reason: Explanation for the mismatch (default: "no_sample_level_pair").
    """
    _ensure_log_dirs()

    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "sample_id": sample_id,
        "expression_source": expression_source,
        "metabolite_source": metabolite_source,
        "reason": reason
    }

    # Load existing entries if file exists
    entries = []
    if DATA_PAIRING_LOG.exists():
        try:
            with open(DATA_PAIRING_LOG, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    entries = data
                elif isinstance(data, dict):
                    # If it's a single entry, wrap it
                    entries = [data]
        except (json.JSONDecodeError, IOError):
            # If file is corrupted or empty, start fresh
            entries = []

    entries.append(entry)

    # Write back
    with open(DATA_PAIRING_LOG, 'w', encoding='utf-8') as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

def log_data_pairing_mismatches_batch(
    mismatches: List[Dict[str, str]]
) -> None:
    """
    Log multiple data pairing mismatches at once.

    Args:
        mismatches: List of dicts with keys: sample_id, expression_source,
                    metabolite_source, reason.
    """
    for mismatch in mismatches:
        log_data_pairing_mismatch(
            sample_id=mismatch.get("sample_id", ""),
            expression_source=mismatch.get("expression_source", ""),
            metabolite_source=mismatch.get("metabolite_source", ""),
            reason=mismatch.get("reason", "no_sample_level_pair")
        )

def get_pairing_log_stats() -> Dict[str, Any]:
    """
    Get statistics about the data pairing log.

    Returns:
        Dict with total_mismatches, unique_sample_ids, and reason_counts.
    """
    if not DATA_PAIRING_LOG.exists():
        return {
            "total_mismatches": 0,
            "unique_sample_ids": 0,
            "reason_counts": {}
        }

    try:
        with open(DATA_PAIRING_LOG, 'r', encoding='utf-8') as f:
            entries = json.load(f)
    except (json.JSONDecodeError, IOError):
        return {
            "total_mismatches": 0,
            "unique_sample_ids": 0,
            "reason_counts": {}
        }

    if not isinstance(entries, list):
        return {
            "total_mismatches": 0,
            "unique_sample_ids": 0,
            "reason_counts": {}
        }

    unique_ids = set()
    reason_counts = {}

    for entry in entries:
        if "sample_id" in entry:
            unique_ids.add(entry["sample_id"])
        reason = entry.get("reason", "unknown")
        reason_counts[reason] = reason_counts.get(reason, 0) + 1

    return {
        "total_mismatches": len(entries),
        "unique_sample_ids": len(unique_ids),
        "reason_counts": reason_counts
    }

def log_zero_variance_feature(
    gene_id: str,
    variance: float,
    reason: str = "zero_variance"
) -> None:
    """
    Log a single zero-variance feature to logs/feature_filtering.csv.

    Args:
        gene_id: The gene identifier.
        variance: The calculated variance (should be < 1e-10).
        reason: Explanation for filtering (default: "zero_variance").
    """
    _ensure_log_dirs()

    file_exists = FEATURE_FILTERING_LOG.exists()

    with open(FEATURE_FILTERING_LOG, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            # Write header
            writer.writerow(["gene_id", "variance", "reason"])

        writer.writerow([gene_id, f"{variance:.2e}", reason])

def log_zero_variance_features_batch(
    features: List[Dict[str, Any]]
) -> None:
    """
    Log multiple zero-variance features at once.

    Args:
        features: List of dicts with keys: gene_id, variance, reason.
    """
    file_exists = FEATURE_FILTERING_LOG.exists()

    with open(FEATURE_FILTERING_LOG, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            # Write header
            writer.writerow(["gene_id", "variance", "reason"])

        for feature in features:
            writer.writerow([
                feature.get("gene_id", ""),
                f"{feature.get('variance', 0):.2e}",
                feature.get("reason", "zero_variance")
            ])

def get_filtering_log_stats() -> Dict[str, Any]:
    """
    Get statistics about the feature filtering log.

    Returns:
        Dict with total_filtered, unique_genes, and reason_counts.
    """
    if not FEATURE_FILTERING_LOG.exists():
        return {
            "total_filtered": 0,
            "unique_genes": 0,
            "reason_counts": {}
        }

    try:
        with open(FEATURE_FILTERING_LOG, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except (IOError, csv.Error):
        return {
            "total_filtered": 0,
            "unique_genes": 0,
            "reason_counts": {}
        }

    unique_genes = set()
    reason_counts = {}

    for row in rows:
        if "gene_id" in row:
            unique_genes.add(row["gene_id"])
        reason = row.get("reason", "unknown")
        reason_counts[reason] = reason_counts.get(reason, 0) + 1

    return {
        "total_filtered": len(rows),
        "unique_genes": len(unique_genes),
        "reason_counts": reason_counts
    }

def main():
    """
    Main function for testing logging utilities.
    Demonstrates logging of pairing mismatches and zero-variance features.
    """
    import sys
    import traceback

    print("Testing logging utilities...")

    try:
        # Test pairing mismatch logging
        print("\n1. Testing data pairing mismatch logging...")
        log_data_pairing_mismatch(
            sample_id="SAMPLE_001",
            expression_source="geo_GSE12345",
            metabolite_source="mw_67890",
            reason="no_sample_level_pair"
        )
        log_data_pairing_mismatch(
            sample_id="SAMPLE_002",
            expression_source="geo_GSE12345",
            metabolite_source="mw_67890",
            reason="sample_id_mismatch"
        )

        stats = get_pairing_log_stats()
        print(f"   Pairing log stats: {stats}")

        # Test batch pairing mismatch logging
        print("\n2. Testing batch data pairing mismatch logging...")
        batch_mismatches = [
            {
                "sample_id": "SAMPLE_003",
                "expression_source": "geo_GSE12345",
                "metabolite_source": "mw_67890",
                "reason": "missing_metabolite_data"
            },
            {
                "sample_id": "SAMPLE_004",
                "expression_source": "geo_GSE12345",
                "metabolite_source": "mw_67890",
                "reason": "missing_expression_data"
            }
        ]
        log_data_pairing_mismatches_batch(batch_mismatches)
        stats = get_pairing_log_stats()
        print(f"   Pairing log stats after batch: {stats}")

        # Test zero-variance feature logging
        print("\n3. Testing zero-variance feature logging...")
        log_zero_variance_feature(
            gene_id="AT1G01010",
            variance=0.0,
            reason="zero_variance"
        )
        log_zero_variance_feature(
            gene_id="AT1G01020",
            variance=1e-15,
            reason="near_zero_variance"
        )

        stats = get_filtering_log_stats()
        print(f"   Filtering log stats: {stats}")

        # Test batch zero-variance feature logging
        print("\n4. Testing batch zero-variance feature logging...")
        batch_features = [
            {"gene_id": "AT1G01030", "variance": 0.0, "reason": "zero_variance"},
            {"gene_id": "AT1G01040", "variance": 0.0, "reason": "zero_variance"},
            {"gene_id": "AT1G01050", "variance": 5e-11, "reason": "low_variance"}
        ]
        log_zero_variance_features_batch(batch_features)
        stats = get_filtering_log_stats()
        print(f"   Filtering log stats after batch: {stats}")

        print("\n✓ All logging utility tests passed.")
        return 0

    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
