"""
Logging utilities for the plant defense compound prediction pipeline.

This module provides functions to log data pairing mismatches and 
feature filtering events to structured log files.

Logs:
    - logs/data_pairing.json: Records sample mismatches during pairing
    - logs/feature_filtering.csv: Records zero-variance genes filtered out
"""
import json
import csv
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Log file paths
PAIRING_LOG_PATH = LOGS_DIR / "data_pairing.json"
FILTERING_LOG_PATH = LOGS_DIR / "feature_filtering.csv"

# Set up module logger
_logger = logging.getLogger(__name__)


def _load_pairing_log() -> List[Dict[str, Any]]:
    """Load existing pairing log entries from JSON file."""
    if PAIRING_LOG_PATH.exists():
        try:
            with open(PAIRING_LOG_PATH, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            _logger.warning(f"Failed to load existing pairing log: {e}. Starting fresh.")
            return []
    return []


def _save_pairing_log(entries: List[Dict[str, Any]]) -> None:
    """Save pairing log entries to JSON file."""
    with open(PAIRING_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


def log_mismatch(sample_id: str, reason: str, 
                 expression_source: Optional[str] = None,
                 metabolite_source: Optional[str] = None) -> None:
    """
    Log a data pairing mismatch to the pairing log file.
    
    Args:
        sample_id: The sample identifier that failed to pair
        reason: The reason for the mismatch (e.g., "no_sample_level_pair")
        expression_source: Optional source identifier for expression data
        metabolite_source: Optional source identifier for metabolite data
    """
    entries = _load_pairing_log()
    
    entry = {
        "sample_id": sample_id,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat(),
        "expression_source": expression_source,
        "metabolite_source": metabolite_source
    }
    
    entries.append(entry)
    _save_pairing_log(entries)
    _logger.debug(f"Logged pairing mismatch for sample {sample_id}: {reason}")


def log_mismatches_batch(mismatches: List[Dict[str, Any]]) -> None:
    """
    Log multiple pairing mismatches at once.
    
    Args:
        mismatches: List of dictionaries with keys: sample_id, reason, 
                   expression_source (optional), metabolite_source (optional)
    """
    existing = _load_pairing_log()
    
    for mismatch in mismatches:
        entry = {
            "sample_id": mismatch.get("sample_id"),
            "reason": mismatch.get("reason"),
            "timestamp": datetime.utcnow().isoformat(),
            "expression_source": mismatch.get("expression_source"),
            "metabolite_source": mismatch.get("metabolite_source")
        }
        existing.append(entry)
    
    _save_pairing_log(existing)
    _logger.debug(f"Logged {len(mismatches)} pairing mismatches in batch")


def get_pairing_log_stats() -> Dict[str, Any]:
    """
    Get statistics from the pairing log.
    
    Returns:
        Dictionary with counts and breakdown by reason
    """
    entries = _load_pairing_log()
    
    if not entries:
        return {
            "total_mismatches": 0,
            "by_reason": {},
            "log_file": str(PAIRING_LOG_PATH)
        }
    
    reason_counts: Dict[str, int] = {}
    for entry in entries:
        reason = entry.get("reason", "unknown")
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
    
    return {
        "total_mismatches": len(entries),
        "by_reason": reason_counts,
        "log_file": str(PAIRING_LOG_PATH)
    }


def _load_filtering_log() -> List[Dict[str, Any]]:
    """Load existing filtering log entries from CSV file."""
    if FILTERING_LOG_PATH.exists():
        try:
            rows = []
            with open(FILTERING_LOG_PATH, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert variance back to float
                    if 'variance' in row:
                        try:
                            row['variance'] = float(row['variance'])
                        except (ValueError, TypeError):
                            row['variance'] = 0.0
                    rows.append(row)
            return rows
        except (IOError, csv.Error) as e:
            _logger.warning(f"Failed to load existing filtering log: {e}. Starting fresh.")
            return []
    return []


def _save_filtering_log(entries: List[Dict[str, Any]]) -> None:
    """Save filtering log entries to CSV file."""
    if not entries:
        # Create empty file with headers if no entries
        with open(FILTERING_LOG_PATH, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['gene_id', 'variance', 'reason', 'timestamp'])
            writer.writeheader()
        return

    fieldnames = ['gene_id', 'variance', 'reason', 'timestamp']
    with open(FILTERING_LOG_PATH, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(entries)


def log_filter(gene_id: str, variance: float, 
               reason: str = "zero_variance") -> None:
    """
    Log a filtered gene to the feature filtering log file.
    
    Args:
        gene_id: The gene identifier that was filtered
        variance: The variance value of the gene
        reason: The reason for filtering (default: "zero_variance")
    """
    entries = _load_filtering_log()
    
    entry = {
        "gene_id": gene_id,
        "variance": variance,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    entries.append(entry)
    _save_filtering_log(entries)
    _logger.debug(f"Logged filtered gene {gene_id} with variance {variance}")


def log_filters_batch(filters: List[Dict[str, Any]], 
                      summary: Optional[Dict[str, Any]] = None) -> None:
    """
    Log multiple filtered genes at once, with optional summary row.
    
    Args:
        filters: List of dictionaries with keys: gene_id, variance, reason (optional)
        summary: Optional summary dictionary to append at the end with 
                gene_id="SUMMARY", variance=<count>, reason="total_removed"
    """
    existing = _load_filtering_log()
    
    for filter_entry in filters:
        entry = {
            "gene_id": filter_entry.get("gene_id"),
            "variance": float(filter_entry.get("variance", 0.0)),
            "reason": filter_entry.get("reason", "zero_variance"),
            "timestamp": datetime.utcnow().isoformat()
        }
        existing.append(entry)
    
    if summary:
        summary_entry = {
            "gene_id": "SUMMARY",
            "variance": float(summary.get("count", len(filters))),
            "reason": "total_removed",
            "timestamp": datetime.utcnow().isoformat()
        }
        existing.append(summary_entry)
    
    _save_filtering_log(existing)
    _logger.debug(f"Logged {len(filters)} filtered genes in batch")


def get_filtering_log_stats() -> Dict[str, Any]:
    """
    Get statistics from the filtering log.
    
    Returns:
        Dictionary with counts and breakdown by reason
    """
    entries = _load_filtering_log()
    
    if not entries:
        return {
            "total_filtered": 0,
            "by_reason": {},
            "log_file": str(FILTERING_LOG_PATH)
        }
    
    reason_counts: Dict[str, int] = {}
    total_variance = 0.0
    for entry in entries:
        reason = entry.get("reason", "unknown")
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
        if entry.get("gene_id") != "SUMMARY":
            total_variance += entry.get("variance", 0.0)
    
    return {
        "total_filtered": len(entries),
        "by_reason": reason_counts,
        "total_variance_removed": total_variance,
        "log_file": str(FILTERING_LOG_PATH)
    }


def clear_pairing_log() -> None:
    """Clear the pairing log file."""
    _save_pairing_log([])
    _logger.info("Cleared pairing log")


def clear_filtering_log() -> None:
    """Clear the filtering log file."""
    _save_filtering_log([])
    _logger.info("Cleared filtering log")


def main() -> None:
    """
    Main function to demonstrate logging utilities.
    This is primarily for testing the logging infrastructure.
    """
    print("Testing logging utilities...")
    
    # Test pairing log
    log_mismatch("SAMPLE_001", "no_sample_level_pair", 
                expression_source="GSE21857", metabolite_source="ST002565")
    log_mismatch("SAMPLE_002", "no_sample_level_pair", 
                expression_source="GSE167633")
    
    stats = get_pairing_log_stats()
    print(f"Pairing log stats: {stats}")
    
    # Test filtering log
    log_filter("AT1G01010", 0.0, "zero_variance")
    log_filter("AT1G01020", 1e-15, "zero_variance")
    log_filters_batch(
        [{"gene_id": "AT1G01030", "variance": 0.0}, 
         {"gene_id": "AT1G01040", "variance": 0.0}],
        summary={"count": 2}
    )
    
    filter_stats = get_filtering_log_stats()
    print(f"Filtering log stats: {filter_stats}")
    
    print("Logging utilities test completed.")


if __name__ == "__main__":
    main()