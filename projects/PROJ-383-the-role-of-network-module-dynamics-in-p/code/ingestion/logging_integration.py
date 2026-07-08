import logging
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from utils.logging_config import setup_logging, log_subject_exclusion, log_memory_usage

def log_missing_behavioral_scores(
    subject_id: str,
    missing_files: List[str],
    logger: Optional[logging.Logger] = None,
) -> None:
    """
    Log exclusion due to missing behavioral data.
    """
    if logger is None:
        logger = logging.getLogger("llmXive")
    
    details = {"missing_files": missing_files}
    log_subject_exclusion(subject_id, "Missing behavioral scores", details, logger)

def log_excessive_motion(
    subject_id: str,
    mean_fd: float,
    threshold: float = 0.2,
    logger: Optional[logging.Logger] = None,
) -> None:
    """
    Log exclusion due to excessive motion.
    """
    if logger is None:
        logger = logging.getLogger("llmXive")
    
    details = {"mean_fd": mean_fd, "threshold": threshold}
    log_subject_exclusion(subject_id, "Excessive motion", details, logger)

def log_subject_processing(
    subject_id: str,
    status: str,
    details: Optional[Dict[str, Any]] = None,
    logger: Optional[logging.Logger] = None,
) -> None:
    """
    Log general processing status for a subject.
    """
    if logger is None:
        logger = logging.getLogger("llmXive")
    
    if status == "excluded":
        reason = details.get("reason", "Unknown")
        log_subject_exclusion(subject_id, reason, details, logger)
    else:
        logger.info(f"Subject {subject_id} processed successfully: {status}", extra={"subject_id": subject_id, "status": status})

def get_exclusion_summary(logger: Optional[logging.Logger] = None) -> Dict[str, int]:
    """
    Retrieve summary of exclusions from the log.
    """
    from utils.logging_config import get_exclusion_summary as get_summary
    return get_summary(logger)

def main():
    """
    CLI test for logging integration.
    """
    setup_logging()
    logger = logging.getLogger("llmXive")
    
    log_missing_behavioral_scores("sub-001", ["nback.csv"])
    log_excessive_motion("sub-002", 0.35)
    log_subject_processing("sub-003", "success", {"frames": 120})
    
    summary = get_exclusion_summary(logger)
    logger.info(f"Current Exclusion Summary: {summary}")
    print("Logging integration test complete.")

if __name__ == "__main__":
    main()
