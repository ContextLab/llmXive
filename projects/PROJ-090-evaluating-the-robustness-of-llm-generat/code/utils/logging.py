"""
Logging infrastructure for the research pipeline.
Captures raw scores, perturbation types, and execution errors.
"""
import logging
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List

from config import ensure_directories

LOG_DIR = Path("data/logs")
DATA_PROCESSED_DIR = Path("data/processed")

# Ensure directories exist on import
ensure_directories()

def init_logging():
    """Initialize the logging infrastructure."""
    # Create logger
    logger = logging.getLogger("llmXive")
    logger.setLevel(logging.DEBUG)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # File handler
    LOG_FILE = LOG_DIR / "pipeline.log"
    fh = logging.FileHandler(LOG_FILE, mode='a')
    fh.setLevel(logging.DEBUG)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

def get_perturbation_logger():
    """Get the perturbation-specific logger."""
    logger = logging.getLogger("llmXive.perturbation")
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(LOG_DIR / "perturbations.log", mode='a')
        fh.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        logger.addHandler(fh)
        logger.addHandler(ch)
    return logger

def get_execution_logger():
    """Get the execution-specific logger."""
    logger = logging.getLogger("llmXive.execution")
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(LOG_DIR / "execution.log", mode='a')
        fh.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        logger.addHandler(fh)
        logger.addHandler(ch)
    return logger

def get_inference_logger():
    """Get the inference-specific logger."""
    logger = logging.getLogger("llmXive.inference")
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(LOG_DIR / "inference.log", mode='a')
        fh.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        logger.addHandler(fh)
        logger.addHandler(ch)
    return logger

def get_budget_logger():
    """Get the budget-specific logger."""
    logger = logging.getLogger("llmXive.budget")
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(LOG_DIR / "budget.log", mode='a')
        fh.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        logger.addHandler(fh)
        logger.addHandler(ch)
    return logger

def _write_json_log_entry(file_path: Path, entry: Dict[str, Any]):
    """Append a JSON entry to a log file (newline-delimited JSON)."""
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')

def log_perturbation_candidate(task_id: str, perturbation_type: str, raw_score: float, is_valid: bool, reason: str = ""):
    """
    Log a perturbation candidate to both the log file and the structured JSON candidates file.
    Captures raw scores, perturbation types, and validity status.
    """
    logger = get_perturbation_logger()
    logger.info(f"Candidate: task_id={task_id}, type={perturbation_type}, score={raw_score:.4f}, valid={is_valid}, reason={reason}")

    # Write to structured JSON for downstream analysis (T018 requirement)
    entry = {
        "timestamp": datetime.now().isoformat(),
        "task_id": task_id,
        "perturbation_type": perturbation_type,
        "raw_score": raw_score,
        "is_valid": is_valid,
        "reason": reason
    }
    _write_json_log_entry(DATA_PROCESSED_DIR / "perturbation_candidates.json", entry)

def log_excluded_perturbation(task_id: str, perturbation_type: str, raw_score: float, reason: str):
    """Log an excluded perturbation."""
    logger = get_perturbation_logger()
    logger.warning(f"Excluded: task_id={task_id}, type={perturbation_type}, score={raw_score:.4f}, reason={reason}")

def log_execution_result(task_id: str, status: str, error_type: Optional[str] = None):
    """
    Log an execution result including raw status and error classification.
    """
    logger = get_execution_logger()
    msg = f"Result: task_id={task_id}, status={status}"
    if error_type:
        msg += f", error={error_type}"
    logger.info(msg)

def log_inference_event(task_id: str, event_type: str, details: Dict[str, Any]):
    """Log an inference event."""
    logger = get_inference_logger()
    logger.info(f"Inference: task_id={task_id}, event={event_type}, details={details}")

def log_budget_update(current_count: int, max_count: int):
    """Log a budget update."""
    logger = get_budget_logger()
    logger.info(f"Budget: current={current_count}, max={max_count}, remaining={max_count - current_count}")

def setup_logger():
    """
    Set up a logger that writes JSON‑lines to ``data/logs/app.log``.
    The logger is named ``app`` and records each log entry as a JSON object
    containing a timestamp, level, logger name, and the log message.
    A single informational entry is emitted so that the file is guaranteed
    to contain at least one JSON line after ``setup_logger()`` is called.
    Returns the configured logger instance.
    """
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)

    # Remove any existing handlers to avoid duplicate writes
    logger.handlers.clear()

    log_path = LOG_DIR / "app.log"
    # Ensure the log directory exists (already handled by ``ensure_directories``)
    file_handler = logging.FileHandler(log_path, mode='a')
    file_handler.setLevel(logging.INFO)

    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            return json.dumps(log_record)

    file_handler.setFormatter(JsonFormatter())
    logger.addHandler(file_handler)

    # Emit a single entry so the file is not empty
    logger.info("app logger initialized")
    return logger

# Initialize logging on module import
init_logging()
