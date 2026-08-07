"""
audit_logger.py

Audit logging infrastructure to capture skipped files, ambiguous prompts, and events.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import LOGS_DIR

_audit_log_path = LOGS_DIR / "audit_log.json"
_logger = logging.getLogger(__name__)

def _load_audit_log() -> List[Dict[str, Any]]:
    """Loads the audit log from disk."""
    if _audit_log_path.exists():
        with open(_audit_log_path, 'r') as f:
            return json.load(f)
    return []

def _save_audit_log(log: List[Dict[str, Any]]):
    """Saves the audit log to disk."""
    with open(_audit_log_path, 'w') as f:
        json.dump(log, f, indent=2)

def clear_audit_logs():
    """Clears the audit log file."""
    if _audit_log_path.exists():
        _audit_log_path.unlink()
    _logger.info("Audit logs cleared.")

def log_skipped_file(file_id: str, reason: str):
    """Logs a skipped file event."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": "SKIPPED_FILE",
        "file_id": file_id,
        "reason": reason
    }
    log = _load_audit_log()
    log.append(log_entry)
    _save_audit_log(log)
    _logger.warning(f"Skipped file {file_id}: {reason}")

def log_ambiguous_prompt(prompt_id: str, reason: str):
    """Logs an ambiguous prompt event."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": "AMBIGUOUS_PROMPT",
        "prompt_id": prompt_id,
        "reason": reason
    }
    log = _load_audit_log()
    log.append(log_entry)
    _save_audit_log(log)
    _logger.warning(f"Ambiguous prompt {prompt_id}: {reason}")

def log_audit_event(event_type: str, entity_id: str, details: str = ""):
    """Logs a general audit event."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "entity_id": entity_id,
        "details": details
    }
    log = _load_audit_log()
    log.append(log_entry)
    _save_audit_log(log)
    _logger.info(f"Audit event: {event_type} for {entity_id}: {details}")

def get_audit_summary() -> Dict[str, Any]:
    """Returns a summary of the audit log."""
    log = _load_audit_log()
    summary = {
        "total_events": len(log),
        "skipped_files": sum(1 for e in log if e["event_type"] == "SKIPPED_FILE"),
        "ambiguous_prompts": sum(1 for e in log if e["event_type"] == "AMBIGUOUS_PROMPT"),
        "other_events": sum(1 for e in log if e["event_type"] not in ["SKIPPED_FILE", "AMBIGUOUS_PROMPT"])
    }
    return summary
