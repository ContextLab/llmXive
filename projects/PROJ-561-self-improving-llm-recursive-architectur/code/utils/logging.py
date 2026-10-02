"""
Logging utilities for the self-improving LLM pipeline.
Implements structured JSON logging and Authority Trace logging for modification proposals.
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

# Import config to access paths and constraints
from config import get_config

# Ensure the logs directory exists
def _ensure_log_dir():
    config = get_config()
    log_dir = Path(config.log_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

def init_cycle_logger(cycle_id: int) -> logging.Logger:
    """
    Initialize a logger for a specific refinement cycle.
    Returns a logger configured to write JSON logs to a cycle-specific file.
    """
    log_dir = _ensure_log_dir()
    log_file = log_dir / f"cycle_{cycle_id}.log"
    
    logger = logging.getLogger(f"cycle_{cycle_id}")
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers = []
    
    # Create file handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    
    # Create formatter that outputs JSON
    formatter = logging.Formatter('%(message)s')
    fh.setFormatter(formatter)
    
    logger.addHandler(fh)
    return logger

def log_cycle_event(logger: logging.Logger, event_type: str, data: Dict[str, Any]) -> None:
    """
    Log a structured event to the cycle logger.
    """
    event_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "data": data
    }
    logger.info(json.dumps(event_data))

def log_authority_trace(
    logger: logging.Logger,
    proposal_id: str,
    benchmark_score: Dict[str, float],
    oracle_result: Dict[str, Any],
    human_constraints: Dict[str, Any]
) -> None:
    """
    Log the 'Authority Trace' for a modification proposal.
    This addresses the 'Source of Authority' concern by explicitly recording:
    1. The specific benchmark score that triggered or validated the proposal.
    2. The result of the External Oracle check.
    3. The human-defined constraints (e.g., parameter limits) that bound the proposal.
    
    Args:
        logger: The cycle logger instance.
        proposal_id: Unique identifier for the proposal.
        benchmark_score: Dict mapping benchmark names to scores (e.g., {'gsm8k': 0.45}).
        oracle_result: Dict containing oracle validation details (pass/fail, reasons).
        human_constraints: Dict of human-imposed limits (e.g., {'max_param_increase_ratio': 0.30}).
    """
    authority_trace = {
        "proposal_id": proposal_id,
        "timestamp": datetime.utcnow().isoformat(),
        "authority_trace": {
            "source_benchmark_scores": benchmark_score,
            "oracle_validation": oracle_result,
            "human_constraints_applied": human_constraints
        }
    }
    
    # Log as a structured JSON message
    logger.info(json.dumps(authority_trace))

def get_log_path(cycle_id: int) -> str:
    """
    Returns the absolute path to the log file for a given cycle.
    """
    config = get_config()
    log_dir = Path(config.log_path).parent
    return str(log_dir / f"cycle_{cycle_id}.log")
