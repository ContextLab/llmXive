import logging
import time
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional
from functools import wraps

from code.config import PROJECT_ROOT, RESULTS_DIR

# Configure logging for the timing module
logger = logging.getLogger("llmxive.timing")
logger.setLevel(logging.INFO)

# Ensure we have a handler if not configured elsewhere
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)

# File path for the timing log
TIMING_LOG_PATH = RESULTS_DIR / "processing_times.jsonl"

def setup_timing_logging():
    """Ensure the results directory exists and initializes the log file."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    if not TIMING_LOG_PATH.exists():
        TIMING_LOG_PATH.touch()
    logger.info(f"Timing log initialized at {TIMING_LOG_PATH}")

def log_document_processing_time(doc_id: str, duration_seconds: float, status: str = "success"):
    """
    Logs the processing time for a single document to a JSONL file.
    
    Args:
        doc_id: Unique identifier for the document.
        duration_seconds: Time taken to process the document in seconds.
        status: 'success' or 'error'.
    """
    entry = {
        "doc_id": doc_id,
        "duration_seconds": duration_seconds,
        "status": status,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    # Write to JSONL file
    with open(TIMING_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    
    # Log to stdout as well
    if duration_seconds >= 60.0:
        logger.warning(f"Document {doc_id} exceeded 60s constraint: {duration_seconds:.2f}s")
    else:
        logger.info(f"Document {doc_id} processed in {duration_seconds:.2f}s (Constraint: <60s)")

def measure_document_processing(doc_id: str):
    """
    Decorator to measure and log the execution time of a document processing function.
    
    Usage:
        @measure_document_processing(doc_id="doc_123")
        def process_my_doc(doc):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                log_document_processing_time(doc_id, duration, "success")
                return result
            except Exception as e:
                duration = time.time() - start_time
                log_document_processing_time(doc_id, duration, "error")
                logger.error(f"Error processing {doc_id}: {str(e)}", exc_info=True)
                raise
        return wrapper
    return decorator

def run_timing_validation():
    """
    Reads the processing times log and validates that all documents 
    were processed within the 60-second constraint.
    """
    if not TIMING_LOG_PATH.exists():
        logger.warning("No timing log found. Run the pipeline first.")
        return False

    violations = []
    total_docs = 0
    
    with open(TIMING_LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            entry = json.loads(line)
            total_docs += 1
            if entry["duration_seconds"] >= 60.0:
                violations.append(entry)
    
    if violations:
        logger.error(f"Validation FAILED: {len(violations)} documents exceeded 60s constraint.")
        for v in violations:
            logger.error(f"  - {v['doc_id']}: {v['duration_seconds']:.2f}s")
        return False
    else:
        logger.info(f"Validation PASSED: All {total_docs} documents processed within 60s.")
        return True

if __name__ == "__main__":
    # Simple test runner if executed directly
    setup_timing_logging()
    log_document_processing_time("test_doc_001", 12.5)
    log_document_processing_time("test_doc_002", 65.0) # Intentional violation for demo
    run_timing_validation()
