import logging
import time
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional
from code.config import RESULTS_DIR

# Configure the specific logger for this module
logger = logging.getLogger("timing_logger")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)

TIMING_LOG_PATH = RESULTS_DIR / "timing_logs.json"

def setup_timing_logging() -> logging.Logger:
    """
    Sets up the logging configuration for timing validation.
    Ensures the log file path is valid and returns the configured logger.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    return logger

def log_document_processing_time(doc_id: str, duration_seconds: float, threshold: float = 60.0) -> None:
    """
    Logs the processing time for a specific document.
    Raises a warning if the duration exceeds the threshold.
    """
    status = "PASS" if duration_seconds <= threshold else "FAIL"
    logger.info(f"Document {doc_id}: {duration_seconds:.4f}s (Threshold: {threshold}s) - {status}")

    log_entry = {
        "doc_id": doc_id,
        "duration_seconds": duration_seconds,
        "threshold_seconds": threshold,
        "status": status,
        "timestamp": time.time()
    }

    # Append to JSONL file for robust logging
    with open(TIMING_LOG_PATH, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

def measure_document_processing(doc_id: str, func: Callable, *args, **kwargs) -> Any:
    """
    Decorator-like wrapper to measure execution time of a document processing function.
    Automatically logs the result.
    """
    start_time = time.perf_counter()
    try:
        result = func(doc_id, *args, **kwargs)
    except Exception as e:
        duration = time.perf_counter() - start_time
        logger.error(f"Document {doc_id} processing failed after {duration:.4f}s: {e}")
        raise
    
    duration = time.perf_counter() - start_time
    log_document_processing_time(doc_id, duration)
    return result

def run_timing_validation() -> Dict[str, Any]:
    """
    Reads the accumulated timing logs and validates the 60s constraint.
    Returns a summary dictionary.
    """
    if not TIMING_LOG_PATH.exists():
        logger.warning("No timing log file found. No validation performed.")
        return {"error": "No log file found"}

    logs = []
    with open(TIMING_LOG_PATH, 'r') as f:
        for line in f:
            if line.strip():
                logs.append(json.loads(line))

    if not logs:
        return {"total_processed": 0, "violations": 0}

    violations = [l for l in logs if l['status'] == 'FAIL']
    
    summary = {
        "total_processed": len(logs),
        "violations": len(violations),
        "avg_duration": sum(l['duration_seconds'] for l in logs) / len(logs),
        "max_duration": max(l['duration_seconds'] for l in logs),
        "constraint_met": len(violations) == 0
    }

    logger.info(f"Timing Validation Summary: {summary}")
    return summary

def main():
    """
    Entry point for running timing validation checks independently.
    """
    setup_timing_logging()
    summary = run_timing_validation()
    if summary.get("constraint_met"):
        logger.info("SUCCESS: All documents processed within 60s constraint.")
        sys.exit(0)
    else:
        logger.error("FAILURE: One or more documents exceeded the 60s constraint.")
        sys.exit(1)

if __name__ == "__main__":
    main()
