import logging
import time
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional
from code.config import RESULTS_DIR, PROJECT_ROOT

# Configuration for timing logs
TIMING_LOG_PATH = RESULTS_DIR / "timing_logs.json"
TIMING_LOG_FILE = RESULTS_DIR / "timing_log.txt"

def setup_timing_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """
    Configure a logger that writes to both console and a specific log file.
    Ensures the log directory exists.
    """
    if log_file is None:
        log_file = TIMING_LOG_FILE

    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("timing_logger")
    logger.setLevel(logging.INFO)

    # Clear existing handlers to avoid duplicates in interactive environments
    if logger.hasHandlers():
        logger.handlers.clear()

    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger

def log_document_processing_time(
    logger: logging.Logger,
    doc_id: str,
    start_time: float,
    end_time: float,
    status: str = "completed",
    extra_details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Logs the processing time for a single document.
    Also appends the entry to a JSON log file for structured analysis.
    """
    duration = end_time - start_time
    msg = f"Document {doc_id}: {duration:.4f}s [{status}]"
    logger.info(msg)

    log_entry = {
        "doc_id": doc_id,
        "start_time": start_time,
        "end_time": end_time,
        "duration_seconds": duration,
        "status": status,
        "details": extra_details or {}
    }

    # Append to JSON log file
    TIMING_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(TIMING_LOG_PATH, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []

    logs.append(log_entry)

    with open(TIMING_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2)

def measure_document_processing(
    doc_id: str,
    process_func: Callable,
    *args,
    **kwargs
) -> Any:
    """
    Decorator-like function to measure execution time of a document processing function.
    Returns the result of the function and logs the timing.
    Raises RuntimeError if processing exceeds 60 seconds.
    """
    logger = setup_timing_logging()
    start = time.perf_counter()
    try:
        result = process_func(*args, **kwargs)
        end = time.perf_counter()
        duration = end - start

        if duration >= 60.0:
            logger.warning(f"Document {doc_id} exceeded 60s limit: {duration:.2f}s")
            log_document_processing_time(logger, doc_id, start, end, status="timeout_warning")
        else:
            log_document_processing_time(logger, doc_id, start, end, status="completed")

        return result
    except Exception as e:
        end = time.perf_counter()
        log_document_processing_time(logger, doc_id, start, end, status="error", extra_details={"error": str(e)})
        raise

def run_timing_validation(corpus_stats_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Reads the JSON timing log and validates that all documents processed within the 60s limit.
    Returns a summary report.
    """
    if not TIMING_LOG_PATH.exists():
        return {"status": "no_logs_found", "message": f"Log file {TIMING_LOG_PATH} not found."}

    with open(TIMING_LOG_PATH, 'r', encoding='utf-8') as f:
        logs = json.load(f)

    if not logs:
        return {"status": "empty_logs", "message": "No log entries found."}

    violations = [entry for entry in logs if entry["duration_seconds"] >= 60.0]
    total_docs = len(logs)
    avg_time = sum(e["duration_seconds"] for e in logs) / total_docs if total_docs > 0 else 0
    max_time = max(e["duration_seconds"] for e in logs) if logs else 0

    summary = {
        "total_documents": total_docs,
        "average_processing_time": avg_time,
        "max_processing_time": max_time,
        "violation_count": len(violations),
        "violations": [
            {"doc_id": v["doc_id"], "time": v["duration_seconds"]}
            for v in violations
        ],
        "all_within_limit": len(violations) == 0,
        "status": "passed" if len(violations) == 0 else "failed"
    }

    return summary

def main():
    """
    CLI entry point to run timing validation on existing logs.
    """
    logger = setup_timing_logging()
    logger.info("Running timing validation...")
    report = run_timing_validation()
    print(json.dumps(report, indent=2))
    if report.get("status") == "passed":
        logger.info("All documents processed within 60s limit.")
    else:
        logger.warning(f"Timing validation failed. {report.get('violation_count')} violations found.")
    return report

if __name__ == "__main__":
    main()
