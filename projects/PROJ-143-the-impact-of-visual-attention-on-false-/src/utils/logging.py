"""
Logging utilities for the visual attention false memory study.

Implements FR-011: Log exclusion reasons for ID mismatches.
Provides functions to log exclusion events and study status updates.
"""
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json

from src.config import get_config


def get_log_path(log_type: str = "exclusion") -> Path:
    """
    Get the path for a specific log file based on the log type.
    
    Args:
        log_type: Type of log ('exclusion', 'study_status', etc.)
        
    Returns:
        Path object pointing to the log file location.
    """
    config = get_config()
    processed_dir = config.paths.processed
    
    log_filename = f"{log_type}_log.jsonl"
    return processed_dir / log_filename


def log_exclusion(
    image_id: str,
    participant_id: str,
    reason: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an exclusion event for ID mismatches per FR-011.
    
    Args:
        image_id: The Visual Genome image ID that was excluded.
        participant_id: The participant ID associated with the exclusion.
        reason: Short code or string describing the exclusion reason.
        details: Optional dictionary with additional context (e.g., expected vs actual IDs).
    """
    log_path = get_log_path("exclusion")
    
    # Ensure parent directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "image_id": image_id,
        "participant_id": participant_id,
        "reason": reason,
        "details": details or {}
    }
    
    # Append as JSONL (one JSON object per line)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def log_study_status(
    status: str,
    message: str,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a study status update (e.g., validation passed, study invalidated).
    
    Args:
        status: Status level (e.g., 'valid', 'invalid', 'inconclusive', 'running').
        message: Human-readable message describing the status.
        metadata: Optional additional context.
    """
    log_path = get_log_path("study_status")
    
    # Ensure parent directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": status,
        "message": message,
        "metadata": metadata or {}
    }
    
    # Append as JSONL
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def main() -> None:
    """
    CLI entry point for logging utilities (for testing/demonstration).
    """
    print("Logging utilities module loaded.")
    print("Available functions: get_log_path, log_exclusion, log_study_status")
    
    # Example usage
    config = get_config()
    print(f"Config loaded from: {config.config_path}")
    print(f"Exclusion log path: {get_log_path('exclusion')}")
    print(f"Study status log path: {get_log_path('study_status')}")