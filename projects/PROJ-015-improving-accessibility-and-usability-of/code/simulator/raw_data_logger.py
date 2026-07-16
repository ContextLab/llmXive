"""
Raw Data Logger for Session Data.

This module handles the logging of raw session data to JSON files in the `data/raw/` directory.
It ensures that the data structure aligns with `contracts/session.schema.yaml` and handles
both complete and incomplete sessions (dropouts).
"""
import json
import hashlib
import uuid
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from utils.logger import get_logger
from config.settings import get_settings
from simulator.data_validator import DataValidator

logger = get_logger(__name__)


class RawDataLogger:
    """
    Handles logging of raw session data to JSON files.
    """

    def __init__(self):
        self.settings = get_settings()
        self.data_dir = Path(self.settings.data_raw_dir)
        self.validator = DataValidator()
        
        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"RawDataLogger initialized. Data directory: {self.data_dir}")

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return str(uuid.uuid4())

    def _generate_checksum(self, data: Dict[str, Any]) -> str:
        """Generate a checksum for the session data."""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode('utf-8')).hexdigest()

    def log_session(
        self,
        participant_id: str,
        disability_type: str,
        interface_type: str,
        sequence: str,
        start_time: datetime,
        end_time: datetime,
        error_count: int,
        explanation_engagement_time_seconds: float,
        sus_score: float,
        status: str,
        dropout_reason: Optional[str] = None
    ) -> str:
        """
        Log a session to a JSON file in data/raw/.

        Args:
            participant_id: Unique identifier for the participant.
            disability_type: Type of disability (e.g., 'visual', 'motor').
            interface_type: Type of interface used ('Traditional' or 'Explainable').
            sequence: Order of interface presentation (e.g., 'Traditional->Explainable').
            start_time: Session start time.
            end_time: Session end time.
            error_count: Number of errors committed during the session.
            explanation_engagement_time_seconds: Time spent engaging with explanations.
            sus_score: System Usability Scale score.
            status: Session status ('complete' or 'incomplete').
            dropout_reason: Reason for dropout if status is 'incomplete'.

        Returns:
            The path to the logged JSON file.

        Raises:
            ValueError: If the session data fails validation.
        """
        session_id = self._generate_session_id()
        
        # Construct the session record
        session_record = {
            "session_id": session_id,
            "participant_id": participant_id,
            "disability_type": disability_type,
            "interface_type": interface_type,
            "sequence": sequence,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "error_count": error_count,
            "explanation_engagement_time_seconds": explanation_engagement_time_seconds,
            "sus_score": sus_score,
            "status": status,
            "dropout_reason": dropout_reason if status == "incomplete" else None
        }

        # Validate the session record
        if not self.validator.validate_session(session_record):
            errors = self.validator.get_last_errors()
            logger.error(f"Session validation failed: {errors}")
            raise ValueError(f"Session data failed validation: {errors}")

        # Generate checksum
        checksum = self._generate_checksum(session_record)
        session_record["checksum"] = checksum

        # Define file path
        file_name = f"session_{session_id}.json"
        file_path = self.data_dir / file_name

        # Write to file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(session_record, f, indent=4)
            
            logger.info(f"Session logged successfully: {file_path}")
            return str(file_path)
        except IOError as e:
            logger.error(f"Failed to write session data to {file_path}: {e}")
            raise

    def log_incomplete_session(
        self,
        participant_id: str,
        disability_type: str,
        interface_type: str,
        sequence: str,
        start_time: datetime,
        end_time: datetime,
        error_count: int,
        explanation_engagement_time_seconds: float,
        sus_score: float,
        dropout_reason: str
    ) -> str:
        """
        Convenience method to log an incomplete session.

        Args:
            participant_id: Unique identifier for the participant.
            disability_type: Type of disability.
            interface_type: Type of interface used.
            sequence: Order of interface presentation.
            start_time: Session start time.
            end_time: Session end time.
            error_count: Number of errors committed.
            explanation_engagement_time_seconds: Time spent engaging with explanations.
            sus_score: System Usability Scale score.
            dropout_reason: Reason for dropout.

        Returns:
            The path to the logged JSON file.
        """
        return self.log_session(
            participant_id=participant_id,
            disability_type=disability_type,
            interface_type=interface_type,
            sequence=sequence,
            start_time=start_time,
            end_time=end_time,
            error_count=error_count,
            explanation_engagement_time_seconds=explanation_engagement_time_seconds,
            sus_score=sus_score,
            status="incomplete",
            dropout_reason=dropout_reason
        )


def main():
    """
    Main function for testing the RawDataLogger.
    """
    logger = get_logger(__name__)
    logger.info("Testing RawDataLogger...")

    logger_instance = RawDataLogger()

    # Test complete session
    try:
        path = logger_instance.log_session(
            participant_id="P001",
            disability_type="visual",
            interface_type="Explainable",
            sequence="Traditional->Explainable",
            start_time=datetime.now(),
            end_time=datetime.now(),
            error_count=2,
            explanation_engagement_time_seconds=15.5,
            sus_score=85.0,
            status="complete"
        )
        logger.info(f"Complete session logged: {path}")
    except Exception as e:
        logger.error(f"Failed to log complete session: {e}")

    # Test incomplete session
    try:
        path = logger_instance.log_incomplete_session(
            participant_id="P002",
            disability_type="motor",
            interface_type="Traditional",
            sequence="Explainable->Traditional",
            start_time=datetime.now(),
            end_time=datetime.now(),
            error_count=5,
            explanation_engagement_time_seconds=0.0,
            sus_score=40.0,
            dropout_reason="Participant requested to stop due to fatigue."
        )
        logger.info(f"Incomplete session logged: {path}")
    except Exception as e:
        logger.error(f"Failed to log incomplete session: {e}")


if __name__ == "__main__":
    main()
