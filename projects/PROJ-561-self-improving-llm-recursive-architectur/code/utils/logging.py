"""
utils/logging.py

Implements structured cycle logging and checkpointing for the self-improving LLM pipeline.
Provides functions to initialize cycle-specific loggers, update logs with metrics,
checkpoint model states, and retrieve cycle history.
"""
import json
import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import shutil

# Import PathConfig from config to ensure consistent paths
from config import get_config

# Constants
LOG_FILE_NAME = "cycle_log.json"
CHECKPOINT_DIR_NAME = "checkpoints"
METRICS_LOG_NAME = "metrics_log.json"

def get_log_path() -> str:
    """
    Returns the absolute path to the project's results directory where logs are stored.
    """
    config = get_config()
    return config.results_path

def _ensure_log_dir():
    """
    Ensures the logging directory exists.
    """
    log_dir = get_log_path()
    os.makedirs(log_dir, exist_ok=True)
    # Also ensure checkpoints subdirectory exists
    checkpoint_dir = os.path.join(log_dir, CHECKPOINT_DIR_NAME)
    os.makedirs(checkpoint_dir, exist_ok=True)

def _get_log_file_path() -> str:
    """
    Returns the full path to the main cycle log file.
    """
    return os.path.join(get_log_path(), LOG_FILE_NAME)

def _get_metrics_file_path() -> str:
    """
    Returns the full path to the metrics log file.
    """
    return os.path.join(get_log_path(), METRICS_LOG_NAME)

def _get_checkpoint_path(cycle_id: int) -> str:
    """
    Returns the full path to a specific cycle's checkpoint directory.
    """
    return os.path.join(get_log_path(), CHECKPOINT_DIR_NAME, f"cycle_{cycle_id}")

def init_cycle_logger(cycle_id: int) -> Dict[str, Any]:
    """
    Initializes a new log entry for a specific cycle.
    Creates the log file if it doesn't exist.
    
    Args:
        cycle_id: The unique integer identifier for the current cycle.
        
    Returns:
        A dictionary representing the initialized cycle log entry.
    """
    _ensure_log_dir()
    log_file = _get_log_file_path()
    
    # Load existing logs if they exist
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    else:
        logs = []
    
    # Check if cycle_id already exists to avoid overwriting
    existing_ids = [entry.get('cycle_id') for entry in logs]
    if cycle_id in existing_ids:
        raise ValueError(f"Cycle ID {cycle_id} already exists in log. Cannot re-initialize.")
    
    new_entry = {
        "cycle_id": cycle_id,
        "start_time": datetime.now().isoformat(),
        "status": "running",
        "metrics": {},
        "modification_proposal": None,
        "error": None,
        "end_time": None,
        "checkpoint_path": _get_checkpoint_path(cycle_id)
    }
    
    logs.append(new_entry)
    
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2)
    
    return new_entry

def update_cycle_log(cycle_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Updates an existing cycle log entry with new metrics or status.
    
    Args:
        cycle_id: The cycle ID to update.
        updates: A dictionary of fields to update (e.g., {"status": "completed", "metrics": {...}}).
                
    Returns:
        The updated log entry.
    """
    _ensure_log_dir()
    log_file = _get_log_file_path()
    
    if not os.path.exists(log_file):
        raise FileNotFoundError(f"Log file {log_file} does not exist.")
    
    with open(log_file, 'r', encoding='utf-8') as f:
        logs = json.load(f)
    
    updated_entry = None
    for i, entry in enumerate(logs):
        if entry['cycle_id'] == cycle_id:
            # Merge updates
            entry.update(updates)
            updated_entry = entry
            logs[i] = entry
            break
    
    if updated_entry is None:
        raise ValueError(f"Cycle ID {cycle_id} not found in log.")
    
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2)
    
    return updated_entry

def checkpoint_model_state(cycle_id: int, model_state_dict: Dict[str, Any], optimizer_state_dict: Optional[Dict[str, Any]] = None) -> str:
    """
    Saves the model and optimizer states to a checkpoint file for a specific cycle.
    
    Args:
        cycle_id: The cycle ID associated with this checkpoint.
        model_state_dict: The state dictionary from torch.nn.Module.state_dict().
        optimizer_state_dict: Optional state dictionary from optimizer.state_dict().
        
    Returns:
        The path to the saved checkpoint file.
    """
    checkpoint_dir = _get_checkpoint_path(cycle_id)
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    checkpoint_file = os.path.join(checkpoint_dir, "model_checkpoint.pt")
    
    checkpoint_data = {
        "cycle_id": cycle_id,
        "timestamp": datetime.now().isoformat(),
        "model_state": model_state_dict
    }
    
    if optimizer_state_dict is not None:
        checkpoint_data["optimizer_state"] = optimizer_state_dict
    
    # Save using torch.save for compatibility with PyTorch models
    import torch
    torch.save(checkpoint_data, checkpoint_file)
    
    # Also update the log to record the checkpoint path
    update_cycle_log(cycle_id, {"checkpoint_path": checkpoint_dir})
    
    return checkpoint_file

def log_cycle_summary(cycle_id: int, summary_data: Dict[str, Any]) -> None:
    """
    Appends a summary entry to a separate metrics log file for easier analysis.
    This is useful for plotting trajectories without parsing the full cycle log.
    
    Args:
        cycle_id: The cycle ID.
        summary_data: A dictionary containing key metrics (e.g., GSM8K accuracy, FLOPs, time).
    """
    _ensure_log_dir()
    metrics_file = _get_metrics_file_path()
    
    if os.path.exists(metrics_file):
        with open(metrics_file, 'r', encoding='utf-8') as f:
            metrics_log = json.load(f)
    else:
        metrics_log = []
    
    summary_entry = {
        "cycle_id": cycle_id,
        "timestamp": datetime.now().isoformat(),
        **summary_data
    }
    
    metrics_log.append(summary_entry)
    
    with open(metrics_file, 'w', encoding='utf-8') as f:
        json.dump(metrics_log, f, indent=2)

def get_cycle_history() -> List[Dict[str, Any]]:
    """
    Retrieves the full history of all logged cycles.
    
    Returns:
        A list of dictionaries, each representing a cycle's log entry.
    """
    _ensure_log_dir()
    log_file = _get_log_file_path()
    
    if not os.path.exists(log_file):
        return []
    
    with open(log_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_metrics_history() -> List[Dict[str, Any]]:
    """
    Retrieves the history of cycle summaries from the metrics log.
    
    Returns:
        A list of dictionaries containing summary metrics for each cycle.
    """
    _ensure_log_dir()
    metrics_file = _get_metrics_file_path()
    
    if not os.path.exists(metrics_file):
        return []
    
    with open(metrics_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def finalize_cycle(cycle_id: int, status: str = "completed", error_msg: Optional[str] = None) -> Dict[str, Any]:
    """
    Finalizes a cycle log entry by setting status, end time, and optional error.
    
    Args:
        cycle_id: The cycle ID to finalize.
        status: Final status string (e.g., "completed", "failed", "timeout").
        error_msg: Optional error message if the cycle failed.
        
    Returns:
        The finalized log entry.
    """
    updates = {
        "status": status,
        "end_time": datetime.now().isoformat()
    }
    if error_msg:
        updates["error"] = error_msg
    
    return update_cycle_log(cycle_id, updates)