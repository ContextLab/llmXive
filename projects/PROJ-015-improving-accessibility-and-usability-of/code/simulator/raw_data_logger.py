"""
Raw data logging module for the accessibility usability study.

This module implements the `RawDataLogger` class which is responsible for
writing session data to `data/raw/` as JSON files. It enforces strict
schema validation (via T019c) and aborts if the schema file is missing
or if validation fails.

Per the project's "No Synthetic Data" policy, this logger is designed
to write real data collected from the web simulator. It does NOT generate
synthetic data.
"""
import json
import hashlib
import uuid
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import the validator from the existing API surface
from simulator.validator import validate_session
from utils.logger import get_logger

logger = get_logger(__name__)

class RawDataLogger:
    """
    Handles writing raw session data to disk with schema validation.

    This logger ensures that:
    1. The schema file (`contracts/session.schema.yaml`) exists.
    2. The data is validated against the schema before writing.
    3. Files are written to `data/raw/` with the naming convention
       `session_{session_id}.json`.
    4. The process aborts (raises exception) if validation fails.
    """

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the RawDataLogger.

        Args:
            output_dir: Directory to write raw session files. Defaults to 'data/raw'.
        """
        self.project_root = Path(__file__).resolve().parent.parent.parent
        self.output_dir = self.project_root / (output_dir or "data/raw")
        self.schema_path = self.project_root / "contracts" / "session.schema.yaml"

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Verify schema file exists (T019b requirement)
        if not self.schema_path.exists():
            raise FileNotFoundError(
                f"Schema file missing at {self.schema_path}. "
                "Task T019b (schema generation) must be completed before logging data."
            )

        logger.info(f"RawDataLogger initialized. Output dir: {self.output_dir}, Schema: {self.schema_path}")

    def _generate_session_id(self, participant_id: str, timestamp: datetime) -> str:
        """
        Generate a unique session ID based on participant ID and timestamp.

        Args:
            participant_id: The unique identifier for the participant.
            timestamp: The timestamp of the session.

        Returns:
            A unique session ID string.
        """
        unique_str = f"{participant_id}_{timestamp.isoformat()}_{uuid.uuid4()}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:12]

    def log_session(self, session_data: Dict[str, Any]) -> str:
        """
        Validate and log a session to a JSON file.

        This method performs the following steps:
        1. Validates the session data against the schema using `validate_session`.
        2. If validation fails, raises a ValueError (abort).
        3. Generates a session ID.
        4. Adds metadata (logged_at) if not present.
        5. Writes the JSON to `data/raw/session_{session_id}.json`.

        Args:
            session_data: Dictionary containing session data conforming to the schema.

        Returns:
            The path to the written file.

        Raises:
            ValueError: If session data fails schema validation.
            FileNotFoundError: If the schema file is missing (checked in __init__).
            IOError: If writing to disk fails.
        """
        # Step 1: Validate data (T019c enforcement)
        # The validator function returns True if valid, but we need to ensure it
        # raises or we handle the failure. Based on T019c description:
        # "If validation fails, raise an exception and do NOT write to data/raw/."
        is_valid = validate_session(session_data)
        
        if not is_valid:
            # This path should theoretically be unreachable if validate_session
            # raises on failure, but we enforce the abort here explicitly.
            raise ValueError(
                "Session data failed schema validation. Aborting write to data/raw/."
            )

        # Step 2: Generate Session ID
        participant_id = session_data.get("participant_id", "unknown")
        start_time = session_data.get("start_time")
        
        # Parse start_time if it's a string, otherwise use current time
        if isinstance(start_time, str):
            try:
                ts = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                ts = datetime.now()
        else:
            ts = datetime.now()

        session_id = self._generate_session_id(participant_id, ts)
        filename = f"session_{session_id}.json"
        file_path = self.output_dir / filename

        # Step 3: Prepare data for writing
        # Ensure all required fields are present and types are correct
        # (Schema validation already checked this, but we ensure JSON serializability)
        output_data = session_data.copy()
        output_data["logged_at"] = datetime.now().isoformat()
        output_data["session_id"] = session_id

        # Step 4: Write to disk
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, default=str)
            logger.info(f"Successfully logged session to {file_path}")
            return str(file_path)
        except IOError as e:
            logger.error(f"Failed to write session data to {file_path}: {e}")
            raise

    def log_sessions_batch(self, sessions: List[Dict[str, Any]]) -> List[str]:
        """
        Log multiple sessions.

        Args:
            sessions: List of session data dictionaries.

        Returns:
            List of paths to written files.

        Raises:
            ValueError: If any session fails validation.
        """
        paths = []
        for i, session in enumerate(sessions):
            try:
                path = self.log_session(session)
                paths.append(path)
            except ValueError as e:
                logger.error(f"Batch log failed at index {i}: {e}")
                raise
        return paths

def main():
    """
    CLI entry point for testing the RawDataLogger.
    This is primarily for verification that the logger works with valid data.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Test RawDataLogger")
    parser.add_argument("--participant_id", type=str, default="test_001", help="Participant ID")
    parser.add_argument("--disability_type", type=str, default="visual", help="Disability type")
    parser.add_argument("--interface_type", type=str, default="explainable", help="Interface type")
    parser.add_argument("--sequence", type=str, default="traditional_explainable", help="Sequence")
    
    args = parser.parse_args()

    logger.info("Running RawDataLogger test...")

    # Construct a valid session data dict based on the schema
    now = datetime.now().isoformat()
    test_data = {
        "participant_id": args.participant_id,
        "disability_type": args.disability_type,
        "interface_type": args.interface_type,
        "sequence": args.sequence,
        "start_time": now,
        "end_time": now,
        "error_count": 0,
        "explanation_engagement_time_seconds": 5.0,
        "sus_score": 100,
        "status": "complete"
    }

    try:
        logger = RawDataLogger()
        path = logger.log_session(test_data)
        print(f"Success: Session logged to {path}")
    except Exception as e:
        print(f"Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()