"""
Audit logging infrastructure for data exclusions (FR-007).

This module provides a structured logging system to record all data exclusions
during the pipeline execution. It ensures traceability and compliance with
Constitution Principle V by writing atomic, append-only audit logs.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Project-specific imports (from T004)
from .versioning import get_project_root, update_state

# Constants
AUDIT_LOG_FILENAME = "audit_log.json"
AUDIT_LOG_DIR = "data/raw"
LOG_FORMAT_VERSION = "1.0"


class AuditLogger:
    """
    A structured audit logger for recording data exclusions and pipeline events.

    Attributes:
        log_path (Path): Full path to the audit log file.
        project_id (str): The project identifier for context.
    """

    def __init__(self, project_id: str = "PROJ-220-predicting-amine-reactivity-using-graph-"):
        """
        Initialize the audit logger.

        Args:
            project_id: The unique identifier for the current project.
        """
        self.project_id = project_id
        self.log_dir = get_project_root() / AUDIT_LOG_DIR
        self.log_path = self.log_dir / AUDIT_LOG_FILENAME

        # Ensure directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Initialize log file if it doesn't exist
        if not self.log_path.exists():
            self._initialize_log_file()

    def _initialize_log_file(self) -> None:
        """Create a new audit log file with a header structure."""
        header = {
            "log_version": LOG_FORMAT_VERSION,
            "project_id": self.project_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "entries": []
        }
        # Write initial structure
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(header, f, indent=2)

    def _load_log(self) -> Dict[str, Any]:
        """
        Load the current log file contents.

        Returns:
            The log dictionary.
        """
        with open(self.log_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_log(self, data: Dict[str, Any]) -> None:
        """
        Atomically save the log data to disk.

        Args:
            data: The log dictionary to save.
        """
        # Write to a temporary file first, then rename (atomic on POSIX)
        temp_path = self.log_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        
        # Atomic rename
        os.replace(temp_path, self.log_path)

    def log_exclusion(
        self,
        reason: str,
        record_id: Optional[str] = None,
        data_source: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "INFO"
    ) -> str:
        """
        Log a data exclusion event.

        This is the primary method for recording why a specific data point
        was excluded from the dataset (e.g., invalid SMILES, missing kinetics).

        Args:
            reason: A human-readable description of the exclusion reason.
            record_id: The unique identifier of the excluded record (if applicable).
            data_source: The source of the data (e.g., "ChEMBL", "PubChem").
            details: Additional structured details about the exclusion.
            severity: The severity level (INFO, WARNING, ERROR).

        Returns:
            The unique ID of the logged entry.
        """
        entry_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        entry = {
            "id": entry_id,
            "timestamp": timestamp,
            "project_id": self.project_id,
            "type": "exclusion",
            "severity": severity,
            "reason": reason,
            "record_id": record_id,
            "data_source": data_source,
            "details": details or {},
            "metadata": {
                "logged_by": "audit_logger",
                "version": LOG_FORMAT_VERSION
            }
        }

        # Load, append, and save
        log_data = self._load_log()
        log_data["entries"].append(entry)
        self._save_log(log_data)

        return entry_id

    def log_event(
        self,
        event_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log a general pipeline event (non-exclusion).

        Args:
            event_type: Type of event (e.g., "START", "END", "ERROR").
            message: Human-readable message.
            details: Additional structured details.

        Returns:
            The unique ID of the logged entry.
        """
        entry_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        entry = {
            "id": entry_id,
            "timestamp": timestamp,
            "project_id": self.project_id,
            "type": "event",
            "event_type": event_type,
            "message": message,
            "details": details or {},
            "metadata": {
                "logged_by": "audit_logger",
                "version": LOG_FORMAT_VERSION
            }
        }

        log_data = self._load_log()
        log_data["entries"].append(entry)
        self._save_log(log_data)

        return entry_id

    def get_exclusion_summary(self) -> Dict[str, int]:
        """
        Get a summary of exclusion counts by reason.

        Returns:
            A dictionary mapping exclusion reasons to their counts.
        """
        log_data = self._load_log()
        summary: Dict[str, int] = {}

        for entry in log_data.get("entries", []):
            if entry.get("type") == "exclusion":
                reason = entry.get("reason", "Unknown")
                summary[reason] = summary.get(reason, 0) + 1

        return summary

    def get_total_exclusions(self) -> int:
        """
        Get the total number of logged exclusions.

        Returns:
            The count of exclusion entries.
        """
        log_data = self._load_log()
        return sum(
            1 for entry in log_data.get("entries", [])
            if entry.get("type") == "exclusion"
        )


# Convenience function for quick logging without explicit instantiation
def log_exclusion(
    reason: str,
    record_id: Optional[str] = None,
    data_source: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    severity: str = "INFO",
    project_id: str = "PROJ-220-predicting-amine-reactivity-using-graph-"
) -> str:
    """
    Quick-log a data exclusion using the default logger instance.

    Args:
        reason: The reason for exclusion.
        record_id: The ID of the excluded record.
        data_source: The source of the data.
        details: Additional details.
        severity: Severity level.
        project_id: The project ID.

    Returns:
        The entry ID.
    """
    logger = AuditLogger(project_id=project_id)
    return logger.log_exclusion(
        reason=reason,
        record_id=record_id,
        data_source=data_source,
        details=details,
        severity=severity
    )
