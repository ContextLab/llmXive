"""
Logging utilities for the recursive self-improving LLM pipeline.
Implements Authority Trace logging to address Source of Authority concerns.
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

# Project root relative to this file (utils/logging.py)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def _ensure_log_dir():
    """Ensure the logs directory exists."""
    log_dir = _PROJECT_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

def get_log_path(cycle_id: int) -> Path:
    """Generate the log file path for a specific cycle."""
    log_dir = _ensure_log_dir()
    return log_dir / f"cycle_{cycle_id:03d}.log"

def init_cycle_logger(cycle_id: int, level: int = logging.INFO) -> logging.Logger:
    """
    Initialize a logger for a specific cycle.
    Returns a logger that writes to a cycle-specific file and stdout.
    """
    log_path = get_log_path(cycle_id)
    logger_name = f"cycle_{cycle_id}"
    
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # File handler
    fh = logging.FileHandler(log_path)
    fh.setLevel(level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    return logger

def log_authority_trace(
    logger: logging.Logger,
    cycle_id: int,
    benchmark_scores: Dict[str, float],
    oracle_result: Dict[str, Any],
    human_constraints: Dict[str, Any]
) -> None:
    """
    Log the 'Authority Trace' for a modification proposal.
    This addresses the Source of Authority concern raised by Ada Lovelace
    and John Von Neumann by explicitly recording the chain of authority:
    1. The specific benchmark scores used for evaluation.
    2. The result of the External Oracle check.
    3. The human-defined constraints (e.g., parameter limits from research.md).
    
    Args:
        logger: The logger instance to use.
        cycle_id: The current cycle number.
        benchmark_scores: Dictionary of benchmark names to scores (e.g., {'GSM8K': 0.45}).
        oracle_result: Dictionary containing oracle validation results.
        human_constraints: Dictionary of human-defined constraints (e.g., {'max_param_increase_ratio': 1.2}).
    """
    trace_data = {
        "cycle_id": cycle_id,
        "timestamp": datetime.utcnow().isoformat(),
        "authority_trace": {
            "benchmark_scores": benchmark_scores,
            "oracle_check": oracle_result,
            "human_constraints": human_constraints
        }
    }
    
    # Format the log message to be human-readable and machine-parseable
    msg_lines = [
        "--- AUTHORITY TRACE START ---",
        f"Cycle ID: {cycle_id}",
        f"Timestamp: {trace_data['timestamp']}",
        "--- Benchmark Scores ---"
    ]
    
    for bench, score in benchmark_scores.items():
        msg_lines.append(f"  {bench}: {score:.4f}")
        
    msg_lines.append("--- Oracle Check ---")
    for key, val in oracle_result.items():
        if isinstance(val, bool):
            msg_lines.append(f"  {key}: {val}")
        elif isinstance(val, dict):
            msg_lines.append(f"  {key}: {json.dumps(val)}")
        else:
            msg_lines.append(f"  {key}: {val}")
            
    msg_lines.append("--- Human Constraints ---")
    for key, val in human_constraints.items():
        msg_lines.append(f"  {key}: {val}")
        
    msg_lines.append("--- AUTHORITY TRACE END ---")
    
    full_msg = "\n".join(msg_lines)
    
    logger.info(full_msg)
    
    # Also write a structured JSON line for programmatic parsing
    json_log_path = _ensure_log_dir() / f"cycle_{cycle_id:03d}_authority.json"
    with open(json_log_path, 'a') as f:
        f.write(json.dumps(trace_data) + "\n")

def log_cycle_summary(
    logger: logging.Logger,
    cycle_id: int,
    summary: Dict[str, Any]
) -> None:
    """
    Log a summary of the cycle results.
    
    Args:
        logger: The logger instance.
        cycle_id: The cycle number.
        summary: Dictionary containing cycle summary metrics.
    """
    logger.info(f"--- CYCLE {cycle_id} SUMMARY ---")
    for key, val in summary.items():
        if isinstance(val, dict):
            logger.info(f"{key}: {json.dumps(val)}")
        else:
            logger.info(f"{key}: {val}")
    logger.info("--- END CYCLE SUMMARY ---")

def log_error(logger: logging.Logger, cycle_id: int, error: Exception, context: Optional[Dict] = None) -> None:
    """
    Log an error with context.
    
    Args:
        logger: The logger instance.
        cycle_id: The cycle number.
        error: The exception that occurred.
        context: Optional dictionary of context variables.
    """
    msg = f"ERROR in Cycle {cycle_id}: {str(error)}"
    if context:
        msg += f" | Context: {json.dumps(context)}"
    logger.error(msg, exc_info=True)

def log_warning(logger: logging.Logger, cycle_id: int, message: str) -> None:
    """
    Log a warning message.
    
    Args:
        logger: The logger instance.
        cycle_id: The cycle number.
        message: The warning message.
    """
    logger.warning(f"[Cycle {cycle_id}] {message}")