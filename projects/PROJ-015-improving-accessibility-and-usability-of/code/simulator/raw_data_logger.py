"""
Raw Data Logger Module for PROJ-015.

This module implements the `RawDataLogger` class to persist session data to
`data/raw/session_{id}.json` upon session completion. It enforces strict
schema validation using the `contracts/session.schema.yaml` file before
writing any data to disk, ensuring data integrity as per EC-001 and FR-006.

Key Responsibilities:
1. Validate incoming session data against the schema.
2. Log complete sessions with status 'complete'.
3. Log partial/dropped sessions with status 'incomplete' and `dropout_reason`.
4. Ensure `contracts/session.schema.yaml` exists before operation.
"""

import json
import hashlib
import uuid
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from utils.logger import get_logger
from config.settings import get_settings
from simulator.data_validator import DataValidator

logger = get_logger(__name__)

class RawDataLogger:
    """
    Handles the persistence of session data to JSON files in data/raw/.

    This class acts as the final sink for the simulator's data collection.
    It requires the `contracts/session.schema.yaml` to be present.
    """

    def __init__(self):
        settings = get_settings()
        self.project_root = settings.project_root
        self.raw_data_dir = self.project_root / "data" / "raw"
        
        # Ensure directory exists
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize validator
        self.validator = DataValidator()
        
        logger.info(f"RawDataLogger initialized. Output directory: {self.raw_data_dir}")

    def _validate_schema_exists(self) -> bool:
        """
        Checks if the required schema file exists.
        Returns True if found, raises FileNotFoundError if missing.
        """
        schema_path = self.project_root / "contracts" / "session.schema.yaml"
        if not schema_path.exists():
            error_msg = f"CRITICAL: Schema file missing at {schema_path}. T019 cannot proceed without T009b."
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        return True

    def log_session(self, session_data: Dict[str, Any]) -> str:
        """
        Validates and logs a session to a JSON file.

        Args:
            session_data: Dictionary containing session metrics. Must include:
                - participant_id
                - disability_type
                - interface_type
                - sequence
                - start_time
                - end_time
                - error_count
                - explanation_engagement_time_seconds
                - sus_score
                - status ('complete' or 'incomplete')
                - dropout_reason (optional, required if status is 'incomplete')

        Returns:
            str: The path to the created JSON file.

        Raises:
            ValueError: If schema validation fails.
            FileNotFoundError: If the schema file is missing.
        """
        # 1. Enforce Schema Existence
        self._validate_schema_exists()

        # 2. Validate Data against Schema
        # The validator will raise ValueError if data is malformed or missing required fields
        is_valid, errors = self.validator.validate_session(session_data)
        
        if not is_valid:
            error_details = f"Session validation failed: {errors}"
            logger.error(error_details)
            # Fail loudly as per constraints: do not log invalid data
            raise ValueError(error_details)

        # 3. Generate Filename
        # Use participant_id or a generated UUID if not present (though schema requires participant_id)
        session_id = session_data.get("participant_id", str(uuid.uuid4()))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"session_{session_id}_{timestamp}.json"
        file_path = self.raw_data_dir / filename

        # 4. Add Metadata
        session_data["logged_at"] = datetime.now().isoformat()
        session_data["file_checksum"] = self._compute_checksum(session_data)

        # 5. Write to Disk
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, default=str)
            
            logger.info(f"Successfully logged session to {file_path}")
            return str(file_path)
        except IOError as e:
            logger.error(f"Failed to write session data to {file_path}: {e}")
            raise e

    def _compute_checksum(self, data: Dict[str, Any]) -> str:
        """
        Computes a SHA-256 checksum of the session data for integrity.
        """
        # Sort keys to ensure deterministic checksum
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()

    def log_dropout(self, participant_id: str, interface_type: str, 
                    sequence: str, dropout_reason: str, 
                    start_time: datetime, end_time: datetime,
                    metrics_partial: Optional[Dict[str, Any]] = None) -> str:
        """
        Helper method to log a session that ended prematurely (dropout).
        Sets status to 'incomplete' and includes the dropout reason.

        Args:
            participant_id: Unique ID for the participant.
            interface_type: The interface used (Traditional/Explainable).
            sequence: The order of interfaces (e.g., "Traditional->Explainable").
            dropout_reason: Reason for leaving (e.g., "Frustration", "Technical Issue").
            start_time: Session start datetime.
            end_time: Session end datetime.
            metrics_partial: Any partial metrics collected before dropout.

        Returns:
            str: Path to the logged JSON file.
        """
        session_data = {
            "participant_id": participant_id,
            "disability_type": metrics_partial.get("disability_type", "unknown") if metrics_partial else "unknown",
            "interface_type": interface_type,
            "sequence": sequence,
            "start_time": start_time.isoformat() if isinstance(start_time, datetime) else str(start_time),
            "end_time": end_time.isoformat() if isinstance(end_time, datetime) else str(end_time),
            "error_count": metrics_partial.get("error_count", 0) if metrics_partial else 0,
            "explanation_engagement_time_seconds": metrics_partial.get("explanation_engagement_time_seconds", 0) if metrics_partial else 0,
            "sus_score": metrics_partial.get("sus_score", None),
            "status": "incomplete",
            "dropout_reason": dropout_reason,
            "metrics_snapshot": metrics_partial or {}
        }

        return self.log_session(session_data)

def main():
    """
    CLI entry point for testing the logger independently.
    """
    import sys
    
    # Mock data for testing
    test_session = {
        "participant_id": "P-TEST-001",
        "disability_type": "visual_impairment",
        "interface_type": "Explainable",
        "sequence": "Explainable->Traditional",
        "start_time": datetime.now().isoformat(),
        "end_time": datetime.now().isoformat(),
        "error_count": 2,
        "explanation_engagement_time_seconds": 15.5,
        "sus_score": 85.0,
        "status": "complete",
        "dropout_reason": None
    }

    logger = get_logger(__name__)
    logger.info("Starting RawDataLogger self-test...")
    
    try:
        logger_instance = RawDataLogger()
        path = logger_instance.log_session(test_session)
        logger.info(f"Self-test passed. File created at: {path}")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Schema missing (Expected if T009b not run): {e}")
        return 1
    except Exception as e:
        logger.error(f"Self-test failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
