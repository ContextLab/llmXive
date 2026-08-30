"""
Failure Logger for Qualitative Failure Analysis (T030).

This module implements logic to compile a qualitative failure log of excluded papers.
It tracks issues such as model substitution, data gaps, and missing variables,
ensuring they are explicitly flagged in the results log as per FR-003.
"""

import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Configure logging for the module
logger = logging.getLogger(__name__)

FAILURE_LOG_PATH = "artifacts/reports/failure_log.json"

class FailureReason:
    """Enumeration of failure reasons as defined in FR-003 and Plan Phase 3."""
    MODEL_SUBSTITUTION = "model_substitution"
    DATA_GAPS = "data_gaps"
    MISSING_VARIABLES = "missing_variables"
    MISSING_SEED = "missing_seed"
    MODEL_UNAVAILABLE = "model_unavailable"
    MANIFEST_INVALID = "manifest_invalid"
    DATA_FETCH_FAILED = "data_fetch_failed"

def load_existing_failure_log(log_path: str = FAILURE_LOG_PATH) -> List[Dict[str, Any]]:
    """
    Loads the existing failure log if it exists, otherwise returns an empty list.
    """
    path = Path(log_path)
    if not path.exists():
        return []
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            logger.warning(f"Failure log at {log_path} is not a list. Resetting.")
            return []
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load failure log from {log_path}: {e}")
        return []

def record_failure(
    paper_id: str,
    reason: str,
    details: str,
    severity: str = "error",
    metadata: Optional[Dict[str, Any]] = None,
    log_path: str = FAILURE_LOG_PATH
) -> None:
    """
    Records a single failure entry to the failure log.
    
    Args:
        paper_id: Unique identifier for the paper (e.g., DOI).
        reason: One of the FailureReason constants.
        details: Human-readable description of the failure.
        severity: 'error', 'warning', or 'info'.
        metadata: Optional additional context (e.g., missing variables list).
        log_path: Path to the failure log file.
    """
    if not paper_id or not reason:
        raise ValueError("paper_id and reason are required to record a failure.")

    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "paper_id": paper_id,
        "reason": reason,
        "details": details,
        "severity": severity,
        "metadata": metadata or {}
    }

    failures = load_existing_failure_log(log_path)
    failures.append(entry)

    # Ensure directory exists
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)

    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(failures, f, indent=2, default=str)
    
    logger.info(f"Recorded failure for {paper_id}: {reason}")

def compile_failure_summary(log_path: str = FAILURE_LOG_PATH) -> Dict[str, Any]:
    """
    Compiles a summary of all failures from the log.
    Returns a dictionary grouped by reason and paper.
    """
    failures = load_existing_failure_log(log_path)
    
    summary = {
        "total_failures": len(failures),
        "by_reason": {},
        "by_paper": {},
        "critical_failures": []
    }

    for entry in failures:
        reason = entry.get("reason", "unknown")
        paper_id = entry.get("paper_id", "unknown")
        
        # Aggregate by reason
        if reason not in summary["by_reason"]:
            summary["by_reason"][reason] = 0
        summary["by_reason"][reason] += 1

        # Aggregate by paper
        if paper_id not in summary["by_paper"]:
            summary["by_paper"][paper_id] = []
        summary["by_paper"][paper_id].append(entry)

        # Track critical failures (e.g., data gaps or model unavailability)
        if reason in [FailureReason.DATA_GAPS, FailureReason.MODEL_UNAVAILABLE, FailureReason.MANIFEST_INVALID]:
            summary["critical_failures"].append(entry)

    return summary

def write_failure_report(report_path: str = "artifacts/reports/failure_summary.json") -> None:
    """
    Writes the compiled failure summary to a JSON report file.
    """
    summary = compile_failure_summary()
    
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Failure summary written to {report_path}")

def main():
    """
    Main entry point for the failure logger script.
    Demonstrates recording a few sample failures and generating the summary.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting Failure Logger (T030)...")

    # Example: Record a model substitution failure
    record_failure(
        paper_id="10.1021/acs.joc.12345",
        reason=FailureReason.MODEL_SUBSTITUTION,
        details="Original model had 1.5M parameters, exceeding 1M limit. Replaced with baseline Random Forest.",
        severity="warning",
        metadata={"original_params": 1500000, "substituted_model": "RandomForest"}
    )

    # Example: Record a data gap failure
    record_failure(
        paper_id="10.1039/C8SC01234A",
        reason=FailureReason.DATA_GAPS,
        details="Supplementary file missing. Required SMILES and Yield columns not found.",
        severity="error",
        metadata={"missing_columns": ["SMILES", "Yield"], "expected_file": "supp_data.csv"}
    )

    # Example: Record a missing seed failure
    record_failure(
        paper_id="10.1002/anie.202012345",
        reason=FailureReason.MISSING_SEED,
        details="Random seed not reported in paper. Defaulted to 42.",
        severity="warning",
        metadata={"default_seed": 42}
    )

    # Write the summary report
    write_failure_report()

    logger.info("Failure Logger completed successfully.")

if __name__ == "__main__":
    main()
