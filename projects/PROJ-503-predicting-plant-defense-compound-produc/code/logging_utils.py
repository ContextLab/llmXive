import json
import csv
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Define absolute paths based on project structure
# Note: These paths are relative to the project root. 
# When running scripts, ensure the CWD is the project root or adjust logic accordingly.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
PAIRING_LOG_PATH = LOGS_DIR / "data_pairing.json"
FILTERING_LOG_PATH = LOGS_DIR / "feature_filtering.csv"

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def _load_pairing_log() -> Dict[str, Any]:
    """Load existing pairing log or initialize a new one."""
    if PAIRING_LOG_PATH.exists():
        with open(PAIRING_LOG_PATH, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                # If corrupted, start fresh but log warning
                return {"mismatches": [], "metadata": {"created": None, "updated": None}}
    return {
        "mismatches": [],
        "metadata": {
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat()
        }
    }


def _save_pairing_log(data: Dict[str, Any]) -> None:
    """Save the pairing log to disk."""
    data["metadata"]["updated"] = datetime.now().isoformat()
    with open(PAIRING_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def log_data_pairing_mismatch(
    sample_id: str,
    expression_source: str,
    metabolite_source: str,
    reason: str = "no_sample_level_pair",
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a single data pairing mismatch to data_pairing.json.
    
    Args:
        sample_id: The identifier of the sample that failed to pair.
        expression_source: Source of the expression data (e.g., GEO accession).
        metabolite_source: Source of the metabolite data (e.g., MW accession).
        reason: Reason for the mismatch (default: "no_sample_level_pair").
        details: Optional additional context (e.g., specific metadata fields).
    """
    log_entry = {
        "sample_id": sample_id,
        "expression_source": expression_source,
        "metabolite_source": metabolite_source,
        "reason": reason,
        "timestamp": datetime.now().isoformat()
    }
    if details:
        log_entry["details"] = details

    log_data = _load_pairing_log()
    log_data["mismatches"].append(log_entry)
    _save_pairing_log(log_data)


def log_data_pairing_mismatches_batch(
    mismatches: List[Dict[str, Any]]
) -> None:
    """
    Log multiple data pairing mismatches at once.
    
    Args:
        mismatches: List of dicts containing mismatch details.
                    Expected keys: sample_id, expression_source, metabolite_source, reason.
    """
    log_data = _load_pairing_log()
    
    for entry in mismatches:
        # Ensure required fields exist
        if not all(k in entry for k in ["sample_id", "expression_source", "metabolite_source", "reason"]):
            continue 
        
        log_entry = {
            "sample_id": entry["sample_id"],
            "expression_source": entry["expression_source"],
            "metabolite_source": entry["metabolite_source"],
            "reason": entry["reason"],
            "timestamp": datetime.now().isoformat()
        }
        if "details" in entry:
            log_entry["details"] = entry["details"]
        
        log_data["mismatches"].append(log_entry)
    
    _save_pairing_log(log_data)


def get_pairing_log_stats() -> Dict[str, Any]:
    """
    Retrieve statistics from the pairing log.
    
    Returns:
        Dict with total mismatches, breakdown by reason, and last updated time.
    """
    if not PAIRING_LOG_PATH.exists():
        return {"total_mismatches": 0, "reasons": {}, "last_updated": None}
    
    log_data = _load_pairing_log()
    mismatches = log_data.get("mismatches", [])
    
    reason_counts = {}
    for m in mismatches:
        reason = m.get("reason", "unknown")
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
    
    return {
        "total_mismatches": len(mismatches),
        "reasons": reason_counts,
        "last_updated": log_data.get("metadata", {}).get("updated")
    }


def _load_filtering_log() -> List[Dict[str, Any]]:
    """Load existing filtering log or initialize a new list."""
    if FILTERING_LOG_PATH.exists():
        rows = []
        with open(FILTERING_LOG_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert variance back to float if present
                if 'variance' in row:
                    try:
                        row['variance'] = float(row['variance'])
                    except ValueError:
                        pass
                rows.append(row)
        return rows
    return []


def _save_filtering_log(rows: List[Dict[str, Any]]) -> None:
    """Save the filtering log to disk (overwrite)."""
    if not rows:
        # Write empty file with headers if no data
        with open(FILTERING_LOG_PATH, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["gene_id", "variance", "reason"])
            writer.writeheader()
        return

    # Ensure headers are consistent
    fieldnames = ["gene_id", "variance", "reason"]
    with open(FILTERING_LOG_PATH, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "gene_id": row.get("gene_id", ""),
                "variance": row.get("variance", 0.0),
                "reason": row.get("reason", "unknown")
            })


def log_zero_variance_feature(
    gene_id: str,
    variance: float,
    reason: str = "zero_variance"
) -> None:
    """
    Log a single zero-variance gene to feature_filtering.csv.
    
    Args:
        gene_id: The identifier of the gene.
        variance: The calculated variance (should be < 1e-10).
        reason: Reason for filtering (default: "zero_variance").
    """
    rows = _load_filtering_log()
    rows.append({
        "gene_id": gene_id,
        "variance": variance,
        "reason": reason
    })
    _save_filtering_log(rows)


def log_zero_variance_features_batch(
    features: List[Dict[str, Any]]
) -> None:
    """
    Log multiple zero-variance features at once.
    
    Args:
        features: List of dicts with keys: gene_id, variance, reason.
    """
    rows = _load_filtering_log()
    
    for entry in features:
        if "gene_id" not in entry or "variance" not in entry:
            continue
        
        rows.append({
            "gene_id": entry["gene_id"],
            "variance": float(entry["variance"]),
            "reason": entry.get("reason", "zero_variance")
        })
    
    _save_filtering_log(rows)


def get_filtering_log_stats() -> Dict[str, Any]:
    """
    Retrieve statistics from the filtering log.
    
    Returns:
        Dict with total filtered genes, breakdown by reason.
    """
    rows = _load_filtering_log()
    
    reason_counts = {}
    for row in rows:
        reason = row.get("reason", "unknown")
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
    
    return {
        "total_filtered": len(rows),
        "reasons": reason_counts
    }
