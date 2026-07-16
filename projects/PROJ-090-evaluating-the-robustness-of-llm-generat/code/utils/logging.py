"""
Logging infrastructure for the research pipeline.
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List

from config import ensure_directories

LOG_DIR = Path("data/logs")
LOG_FILE = LOG_DIR / "pipeline.log"

def init_logging():
    """Initialize the logging infrastructure."""
    ensure_directories()
    
    # Create logger
    logger = logging.getLogger("llmXive")
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # File handler
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

def log_perturbation_candidate(task_id: str, perturbation_type: str, raw_score: float, is_valid: bool, reason: str = ""):
    """Log a perturbation candidate."""
    logger = get_perturbation_logger()
    logger.info(f"Candidate: task_id={task_id}, type={perturbation_type}, score={raw_score:.4f}, valid={is_valid}, reason={reason}")

def log_excluded_perturbation(task_id: str, perturbation_type: str, raw_score: float, reason: str):
    """Log an excluded perturbation."""
    logger = get_perturbation_logger()
    logger.warning(f"Excluded: task_id={task_id}, type={perturbation_type}, score={raw_score:.4f}, reason={reason}")

def log_execution_result(task_id: str, status: str, error_type: Optional[str] = None):
    """Log an execution result."""
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

# Initialize logging on module import
init_logging()
