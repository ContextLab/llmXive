"""
Audit logging infrastructure for capturing skipped files and ambiguous prompts.

This module provides functions to log audit events, skipped files, and ambiguous
prompts during the data processing pipeline. All audit logs are stored in a
centralized JSON file for later analysis and debugging.
"""
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from code.config import AUDIT_LOG_PATH, ENABLE_AUDIT_LOGGING, LOG_LEVEL, LOG_FORMAT, LOG_FILE_PATH

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE_PATH),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global audit state
_audit_state = {
    "events": [],
    "skipped_files": [],
    "ambiguous_prompts": [],
    "start_time": None,
    "end_time": None
}

def _load_audit_state() -> Dict[str, Any]:
    """Load audit state from disk if it exists."""
    if not ENABLE_AUDIT_LOGGING:
        return _audit_state
    
    if AUDIT_LOG_PATH.exists():
        try:
            with open(AUDIT_LOG_PATH, 'r') as f:
                loaded = json.load(f)
                # Merge with current state
                for key in loaded:
                    if key in _audit_state:
                        _audit_state[key].extend(loaded[key])
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load audit log: {e}. Starting fresh.")
    return _audit_state

def _save_audit_state() -> None:
    """Save audit state to disk."""
    if not ENABLE_AUDIT_LOGGING:
        return
    
    try:
        with open(AUDIT_LOG_PATH, 'w') as f:
            json.dump(_audit_state, f, indent=2, default=str)
    except IOError as e:
        logger.error(f"Failed to save audit log: {e}")

def clear_audit_logs() -> None:
    """Clear all audit logs and reset state."""
    global _audit_state
    _audit_state = {
        "events": [],
        "skipped_files": [],
        "ambiguous_prompts": [],
        "start_time": datetime.now().isoformat(),
        "end_time": None
    }
    if AUDIT_LOG_PATH.exists():
        AUDIT_LOG_PATH.unlink()
    logger.info("Audit logs cleared.")

def log_audit_event(event_type: str, details: Dict[str, Any]) -> None:
    """
    Log a general audit event.
    
    Args:
        event_type: Type of event (e.g., "processing_start", "batch_complete")
        details: Additional event details
    """
    if not ENABLE_AUDIT_LOGGING:
        return
    
    event = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "details": details
    }
    _audit_state["events"].append(event)
    _save_audit_state()
    logger.info(f"Audit event: {event_type} - {details}")

def log_skipped_file(file_id: str, reason: str, details: Optional[str] = None) -> None:
    """
    Log a skipped file with reason and details.
    
    Args:
        file_id: Unique identifier for the skipped file
        reason: Reason for skipping (e.g., "low_optical_flow", "corrupted")
        details: Additional details about why the file was skipped
    """
    if not ENABLE_AUDIT_LOGGING:
        return
    
    skipped_entry = {
        "timestamp": datetime.now().isoformat(),
        "file_id": file_id,
        "reason": reason,
        "details": details or ""
    }
    _audit_state["skipped_files"].append(skipped_entry)
    _save_audit_state()
    logger.warning(f"Skipped file: {file_id} - Reason: {reason}")

def log_ambiguous_prompt(prompt_id: str, prompt_text: str, reason: str) -> None:
    """
    Log an ambiguous prompt that couldn't be processed.
    
    Args:
        prompt_id: Unique identifier for the prompt
        prompt_text: The actual prompt text
        reason: Reason why the prompt was considered ambiguous
    """
    if not ENABLE_AUDIT_LOGGING:
        return
    
    ambiguous_entry = {
        "timestamp": datetime.now().isoformat(),
        "prompt_id": prompt_id,
        "prompt_text": prompt_text,
        "reason": reason
    }
    _audit_state["ambiguous_prompts"].append(ambiguous_entry)
    _save_audit_state()
    logger.warning(f"Ambiguous prompt logged: {prompt_id} - Reason: {reason}")

def get_audit_summary() -> Dict[str, Any]:
    """
    Get a summary of the current audit state.
    
    Returns:
        Dictionary containing counts and samples of logged events
    """
    return {
        "total_events": len(_audit_state["events"]),
        "total_skipped_files": len(_audit_state["skipped_files"]),
        "total_ambiguous_prompts": len(_audit_state["ambiguous_prompts"]),
        "start_time": _audit_state["start_time"],
        "end_time": _audit_state["end_time"],
        "recent_skipped_files": _audit_state["skipped_files"][-10:],
        "recent_ambiguous_prompts": _audit_state["ambiguous_prompts"][-10:],
        "skipped_files": _audit_state["skipped_files"],
        "ambiguous_prompts": _audit_state["ambiguous_prompts"],
        "events": _audit_state["events"]
    }

# Initialize audit state on module load
_load_audit_state()
if _audit_state["start_time"] is None:
    _audit_state["start_time"] = datetime.now().isoformat()
