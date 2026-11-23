"""
Session Logger Module

Handles the logging of raw session data to JSON files with schema validation.
"""
import json
import hashlib
import uuid
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Import the validator from the sibling module
try:
    from simulator.validator import load_schema, validate_session
except ImportError:
    # Fallback for direct execution or different import context
    from code.simulator.validator import load_schema, validate_session

from utils.logger import get_logger

logger = get_logger(__name__)

# Project root relative to this file
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_SCHEMA_PATH = _PROJECT_ROOT / "contracts" / "session.schema.yaml"
_RAW_DATA_DIR = _PROJECT_ROOT / "data" / "raw"

class SessionLogger:
    """
    Class to handle session logging with schema validation.
    """
    def __init__(self, schema_path: Optional[Path] = None, data_dir: Optional[Path] = None):
        self.schema_path = schema_path or _SCHEMA_PATH
        self.data_dir = data_dir or _RAW_DATA_DIR
        self._schema = None

        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Load schema at initialization
        if not self.schema_path.exists():
            raise FileNotFoundError(
                f"Schema file not found at {self.schema_path}. "
                "Ensure T019b (contracts/session.schema.yaml) is completed."
            )
        
        self._schema = load_schema(self.schema_path)
        logger.info(f"SessionLogger initialized with schema: {self.schema_path}")

    def log_session(self, data: Dict[str, Any], session_id: Optional[str] = None) -> str:
        """
        Log a session to a JSON file.

        Args:
            data: Dictionary containing session data.
            session_id: Optional session ID. If None, a UUID is generated.

        Returns:
            The path to the created JSON file.

        Raises:
            ValueError: If data fails schema validation.
            FileNotFoundError: If schema is missing.
        """
        # Generate session ID if not provided
        if session_id is None:
            session_id = str(uuid.uuid4())

        # Validate data against schema
        is_valid, errors = validate_session(data, self._schema)
        
        if not is_valid:
            error_msg = f"Session data validation failed for {session_id}: {errors}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Ensure required fields are present (double check)
        required_fields = [
            "participant_id", "disability_type", "interface_type", "sequence",
            "start_time", "end_time", "error_count", "explanation_engagement_time_seconds",
            "sus_score", "status", "dropout_reason"
        ]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field '{field}' in session data for {session_id}")

        # Add metadata
        data["logged_at"] = datetime.utcnow().isoformat()
        data["schema_version"] = "1.0.0"
        
        # Construct file path
        file_path = self.data_dir / f"session_{session_id}.json"
        
        # Write to file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Session logged successfully: {file_path}")
            return str(file_path)
        except IOError as e:
            logger.error(f"Failed to write session file {file_path}: {e}")
            raise

def log_session(data: Dict[str, Any], session_id: Optional[str] = None) -> str:
    """
    Top-level function to log a session.
    
    This function acts as a convenience wrapper around SessionLogger.
    It enforces the requirement to abort if the schema is missing or validation fails.

    Args:
        data: Dictionary containing session data.
        session_id: Optional session ID.

    Returns:
        Path to the created JSON file.

    Raises:
        FileNotFoundError: If schema is missing.
        ValueError: If data fails validation.
    """
    logger = get_logger(__name__)
    
    # Check for schema existence before initializing logger
    schema_path = _PROJECT_ROOT / "contracts" / "session.schema.yaml"
    if not schema_path.exists():
        logger.error(f"Schema file missing at {schema_path}. Aborting log_session.")
        raise FileNotFoundError(
            f"Schema file missing at {schema_path}. "
            "Task T019b must be completed before logging sessions."
        )

    # Initialize logger (which loads schema)
    try:
        session_logger = SessionLogger(schema_path=schema_path)
        return session_logger.log_session(data, session_id)
    except ValueError as e:
        # Re-raise validation errors to ensure the pipeline fails loudly
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in log_session: {e}")
        raise

def main():
    """
    CLI entry point for testing the session logger.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Test session logger.")
    parser.add_argument("--participant-id", type=str, required=True, help="Participant ID")
    parser.add_argument("--disability", type=str, choices=["visual", "motor", "cognitive", "hearing", "none"], default="none")
    parser.add_argument("--interface", type=str, choices=["traditional", "explainable"], default="traditional")
    parser.add_argument("--sequence", type=str, choices=["Traditional->Explainable", "Explainable->Traditional"], default="Traditional->Explainable")
    
    args = parser.parse_args()

    # Construct sample data
    now = datetime.utcnow()
    sample_data = {
        "participant_id": args.participant_id,
        "disability_type": args.disability,
        "interface_type": args.interface,
        "sequence": args.sequence,
        "start_time": now.isoformat(),
        "end_time": now.isoformat(),
        "error_count": 0,
        "explanation_engagement_time_seconds": 0.0 if args.interface == "traditional" else 5.0,
        "sus_score": 80,
        "status": "complete",
        "dropout_reason": None
    }

    try:
        path = log_session(sample_data)
        print(f"Session logged to: {path}")
    except Exception as e:
        print(f"Failed to log session: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
