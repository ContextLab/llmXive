"""
Logging utilities for SDAR pipeline.
Provides a JSON logger that outputs specific metrics required by the SDAR algorithm.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure output directories exist
LOG_DIR = Path("outputs/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

def get_json_logger(
    filename: str = "train_log.json",
    log_dir: Optional[Path] = None,
) -> Any:
    """
    Returns a logger function that appends JSON log entries to a file.

    Args:
        filename: Name of the log file (e.g., 'train_log.json').
        log_dir: Directory to store logs. Defaults to outputs/logs.

    Returns:
        A callable that accepts a dictionary of metrics and appends it to the log file.
    """
    if log_dir is None:
        log_dir = LOG_DIR
    
    log_path = log_dir / filename

    def log_entry(metrics: Dict[str, Any]) -> None:
        """
        Logs a dictionary of metrics as a single JSON line.
        
        Args:
            metrics: Dictionary containing metric keys like 'SDAR Gate Loss', 'RL Loss',
                     'kl_divergence', 'teacher_update_count', 'gate_activation_rate'.
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            **metrics
        }
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    return log_entry

def log_metrics(
    sdar_gate_loss: Optional[float] = None,
    rl_loss: Optional[float] = None,
    kl_divergence: Optional[float] = None,
    teacher_update_count: Optional[int] = None,
    gate_activation_rate: Optional[float] = None,
    step: Optional[int] = None,
) -> Any:
    """
    Factory to create a logger with pre-filled context or a one-shot logging function.
    For this task, we return a function that logs the provided metrics.
    """
    logger = get_json_logger()
    
    def _log(metrics: Dict[str, Any]):
        combined = {}
        if step is not None:
            combined["step"] = step
        if sdar_gate_loss is not None:
            combined["SDAR Gate Loss"] = sdar_gate_loss
        if rl_loss is not None:
            combined["RL Loss"] = rl_loss
        if kl_divergence is not None:
            combined["kl_divergence"] = kl_divergence
        if teacher_update_count is not None:
            combined["teacher_update_count"] = teacher_update_count
        if gate_activation_rate is not None:
            combined["gate_activation_rate"] = gate_activation_rate
        
        # Merge passed metrics (allows overriding or adding extra keys)
        combined.update(metrics)
        logger(combined)

    return _log