"""
Utility functions for simulation logging.

Provides functions to ensure log directories exist and log simulation runs
in JSON format.
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


def ensure_log_directory(log_dir: Optional[str] = None) -> Path:
    """
    Ensure the log directory exists, creating it if necessary.
    
    Args:
        log_dir: Path to log directory. Defaults to 'data/results'.
        
    Returns:
        Path object for the log directory
    """
    if log_dir is None:
        log_dir = "data/results"
    
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    return log_path


def log_simulation_run(log_entry: Dict[str, Any], log_file: Optional[str] = None) -> None:
    """
    Log a simulation run entry to a JSON file.
    
    Args:
        log_entry: Dictionary containing log information
        log_file: Path to log file. Defaults to 'data/results/simulation.log'
    """
    if log_file is None:
        log_file = "data/results/simulation.log"
    
    log_path = Path(log_file)
    
    # Ensure parent directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Add timestamp if not present
    if "timestamp" not in log_entry:
        log_entry["timestamp"] = datetime.now().isoformat()
    
    # Append to log file in JSON Lines format (one JSON object per line)
    with open(log_path, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')


def get_log_entries(log_file: Optional[str] = None) -> list:
    """
    Read all log entries from the log file.
    
    Args:
        log_file: Path to log file. Defaults to 'data/results/simulation.log'
        
    Returns:
        List of log entry dictionaries
    """
    if log_file is None:
        log_file = "data/results/simulation.log"
    
    log_path = Path(log_file)
    
    if not log_path.exists():
        return []
    
    entries = []
    with open(log_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    # Skip malformed lines
                    continue
    
    return entries
