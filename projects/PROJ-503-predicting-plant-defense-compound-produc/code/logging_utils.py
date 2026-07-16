"""
Logging utilities for the plant defense compound prediction pipeline.

Provides functions to log data pairing mismatches and zero-variance feature filtering
events to specific log files as per spec.md edge case requirements.
"""
import json
import csv
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Define project root and log paths relative to the project structure
# The project root is assumed to be the parent of 'code'
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_LOGS_DIR = _PROJECT_ROOT / "logs"
_PAIRING_LOG_PATH = _LOGS_DIR / "data_pairing.json"
_FILTERING_LOG_PATH = _LOGS_DIR / "feature_filtering.csv"

# Ensure logs directory exists
_LOGS_DIR.mkdir(parents=True, exist_ok=True)


def _load_pairing_log() -> List[Dict[str, Any]]:
    """Load existing pairing log or return empty list if file doesn't exist."""
    if not _PAIRING_LOG_PATH.exists():
        return []
    try:
        with open(_PAIRING_LOG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        # If file is corrupted or unreadable, start fresh
        return []


def _save_pairing_log(data: List[Dict[str, Any]]) -> None:
    """Save data to the pairing log JSON file."""
    with open(_PAIRING_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)


def log_data_pairing_mismatch(sample_id: str, expression_source: str, 
                              metabolite_source: str, reason: str = "no_sample_level_pair") -> None:
    """
    Log a single data pairing mismatch event.
    
    Args:
        sample_id: The identifier of the sample that failed to pair.
        expression_source: The source of the expression data (e.g., GEO accession).
        metabolite_source: The source of the metabolite data (e.g., Metabolomics Workbench ID).
        reason: The reason for the mismatch (default: "no_sample_level_pair").
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "sample_id": sample_id,
        "expression_source": expression_source,
        "metabolite_source": metabolite_source,
        "reason": reason
    }
    
    current_log = _load_pairing_log()
    current_log.append(log_entry)
    _save_pairing_log(current_log)


def log_data_pairing_mismatches_batch(mismatches: List[Dict[str, str]]) -> int:
    """
    Log a batch of data pairing mismatch events.
    
    Args:
        mismatches: List of dictionaries containing mismatch details.
                    Each dict should have keys: sample_id, expression_source, 
                    metabolite_source, reason (optional).
                    
    Returns:
        int: The total number of mismatches logged (new + existing).
    """
    current_log = _load_pairing_log()
    
    for mismatch in mismatches:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "sample_id": mismatch.get("sample_id", "unknown"),
            "expression_source": mismatch.get("expression_source", "unknown"),
            "metabolite_source": mismatch.get("metabolite_source", "unknown"),
            "reason": mismatch.get("reason", "no_sample_level_pair")
        }
        current_log.append(entry)
    
    _save_pairing_log(current_log)
    return len(current_log)


def get_pairing_log_stats() -> Dict[str, Any]:
    """
    Retrieve statistics about the current pairing log.
    
    Returns:
        Dictionary with counts and breakdown by reason.
    """
    current_log = _load_pairing_log()
    
    if not current_log:
        return {
            "total_mismatches": 0,
            "reasons": {}
        }
    
    reasons = {}
    for entry in current_log:
        reason = entry.get("reason", "unknown")
        reasons[reason] = reasons.get(reason, 0) + 1
        
    return {
        "total_mismatches": len(current_log),
        "reasons": reasons
    }


def log_zero_variance_feature(gene_id: str, variance: float, reason: str = "zero_variance") -> None:
    """
    Log a single zero-variance feature filtering event.
    
    Args:
        gene_id: The identifier of the gene with zero variance.
        variance: The calculated variance value (should be < 1e-10).
        reason: The reason for filtering (default: "zero_variance").
    """
    # Check if file exists to determine write mode and headers
    file_exists = _FILTERING_LOG_PATH.exists()
    
    with open(_FILTERING_LOG_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["gene_id", "variance", "reason", "timestamp"])
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow({
            "gene_id": gene_id,
            "variance": variance,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })


def log_zero_variance_features_batch(features: List[Dict[str, Any]]) -> int:
    """
    Log a batch of zero-variance feature filtering events.
    
    Args:
        features: List of dictionaries containing feature details.
                  Each dict should have keys: gene_id, variance, reason (optional).
                  
    Returns:
        int: The total number of features logged in this batch.
    """
    file_exists = _FILTERING_LOG_PATH.exists()
    count = 0
    
    with open(_FILTERING_LOG_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["gene_id", "variance", "reason", "timestamp"])
        
        if not file_exists:
            writer.writeheader()
        
        for feature in features:
            writer.writerow({
                "gene_id": feature.get("gene_id", "unknown"),
                "variance": feature.get("variance", 0.0),
                "reason": feature.get("reason", "zero_variance"),
                "timestamp": datetime.now().isoformat()
            })
            count += 1
            
    return count


def get_filtering_log_stats() -> Dict[str, Any]:
    """
    Retrieve statistics about the current filtering log.
    
    Returns:
        Dictionary with counts and breakdown by reason.
    """
    if not _FILTERING_LOG_PATH.exists():
        return {
            "total_filtered": 0,
            "reasons": {}
        }
    
    try:
        with open(_FILTERING_LOG_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except (IOError, csv.Error):
        return {
            "total_filtered": 0,
            "reasons": {}
        }
    
    if not rows:
        return {
            "total_filtered": 0,
            "reasons": {}
        }
    
    reasons = {}
    for row in rows:
        reason = row.get("reason", "unknown")
        reasons[reason] = reasons.get(reason, 0) + 1
        
    return {
        "total_filtered": len(rows),
        "reasons": reasons
    }