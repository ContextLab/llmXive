"""
Raw Data Logger Module for PROJ-015.

Implements the `RawDataLogger` class to handle the serialization of session data
to `data/raw/session_{id}.json` and the generation of SHA-256 checksums for
data integrity verification.

Dependencies:
    - utils.checksum (for checksum generation)
    - models.data_models (for Session data structure)
    - utils.logger (for logging)
    - config.settings (for path configuration)
"""
import json
import hashlib
import uuid
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union

# Local imports based on provided API surface
from utils.logger import get_logger
from utils.checksum import generate_checksum_file
from config.settings import get_settings
from models.data_models import Session

logger = get_logger(__name__)


class RawDataLogger:
    """
    Handles the persistence of raw session data to JSON files with integrity checksums.

    This class ensures that all raw interaction data is written to `data/raw/`
    in an immutable format, immediately followed by the generation of a
    corresponding `.sha256` checksum file.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize the RawDataLogger.

        Args:
            base_dir: Optional base directory for raw data. Defaults to
                      settings.DATA_RAW_DIR.
        """
        settings = get_settings()
        self.base_dir = base_dir or settings.DATA_RAW_DIR
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """Ensure the raw data directory exists."""
        if not self.base_dir.exists():
            logger.info(f"Creating raw data directory: {self.base_dir}")
            self.base_dir.mkdir(parents=True, exist_ok=True)

    def _serialize_session(self, session: Session) -> Dict[str, Any]:
        """
        Convert a Session object to a serializable dictionary.

        Args:
            session: The Session dataclass instance.

        Returns:
            A dictionary representation suitable for JSON serialization.
        """
        # Convert datetime objects to ISO format strings
        data = session.__dict__.copy()
        if 'start_time' in data and data['start_time']:
            data['start_time'] = data['start_time'].isoformat()
        if 'end_time' in data and data['end_time']:
            data['end_time'] = data['end_time'].isoformat()
        
        # Handle nested objects if any (e.g., metrics list)
        # Assuming Session.metrics is a list of Metric objects or dicts
        if 'metrics' in data and data['metrics']:
            processed_metrics = []
            for m in data['metrics']:
                if hasattr(m, '__dict__'):
                    processed_metrics.append(m.__dict__)
                else:
                    processed_metrics.append(m)
            data['metrics'] = processed_metrics

        return data

    def log_session(self, session: Session, session_id: Optional[str] = None) -> Path:
        """
        Log a session to a JSON file and generate a checksum.

        This method:
        1. Generates a unique session ID if not provided.
        2. Serializes the Session object to JSON.
        3. Writes the JSON to `data/raw/session_{id}.json`.
        4. Generates a SHA-256 checksum file `data/raw/session_{id}.json.sha256`.

        Args:
            session: The Session object containing interaction data.
            session_id: Optional explicit session ID. If None, a UUID is generated.

        Returns:
            The Path to the written JSON file.

        Raises:
            FileNotFoundError: If the base directory cannot be created or written to.
            IOError: If writing the file fails.
        """
        if session_id is None:
            session_id = str(uuid.uuid4())

        file_path = self.base_dir / f"session_{session_id}.json"
        checksum_path = self.base_dir / f"session_{session_id}.json.sha256"

        logger.info(f"Logging raw session data to {file_path}")

        try:
            # Serialize
            json_data = self._serialize_session(session)
            
            # Write JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)

            # Generate Checksum
            # Using the utility from utils.checksum which handles the file reading and hashing
            generate_checksum_file(file_path, checksum_path)

            logger.info(f"Successfully logged session {session_id} with checksum.")
            return file_path

        except Exception as e:
            logger.error(f"Failed to log session {session_id}: {e}")
            raise IOError(f"Could not write session data to {file_path}") from e

    def log_raw_dict(self, data: Dict[str, Any], session_id: Optional[str] = None) -> Path:
        """
        Log a raw dictionary to a JSON file and generate a checksum.

        Useful for logging data that hasn't been fully structured into a Session object yet,
        or for custom metadata.

        Args:
            data: Dictionary containing session data.
            session_id: Optional explicit session ID.

        Returns:
            The Path to the written JSON file.
        """
        if session_id is None:
            session_id = str(uuid.uuid4())

        file_path = self.base_dir / f"session_{session_id}.json"
        checksum_path = self.base_dir / f"session_{session_id}.json.sha256"

        logger.info(f"Logging raw dictionary data to {file_path}")

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            generate_checksum_file(file_path, checksum_path)
            logger.info(f"Successfully logged raw data with checksum.")
            return file_path

        except Exception as e:
            logger.error(f"Failed to log raw data: {e}")
            raise IOError(f"Could not write raw data to {file_path}") from e


def main():
    """
    Standalone execution entry point for testing the RawDataLogger.
    
    This function creates a mock Session, logs it, and verifies the checksum file exists.
    It is intended to be run as a script: `python code/simulator/raw_data_logger.py`
    """
    from models.data_models import Participant, Metric
    from datetime import datetime

    logger.info("Running RawDataLogger self-test...")

    # Create a mock participant
    participant = Participant(
        id="P001-MOCK",
        disability_type="visual_impairment",
        interface_sequence=["traditional", "explainable"]
    )

    # Create a mock session
    session = Session(
        session_id="TEST-001",
        participant_id=participant.id,
        interface_type="explainable",
        start_time=datetime.now(),
        end_time=datetime.now(),
        error_count=2,
        explanation_engagement_time_seconds=15.5,
        sus_score=80.0,
        skip_count=0,
        status="complete",
        metrics=[
            Metric(
                metric_name="completion_time",
                interface_type="explainable",
                mean=120.5,
                std_dev=5.2,
                p_value=0.03,
                confidence_interval=[115.0, 126.0],
                test_method="t-test"
            )
        ]
    )

    logger = get_logger(__name__)
    raw_logger = RawDataLogger()

    try:
        output_path = raw_logger.log_session(session)
        logger.info(f"Session logged successfully to: {output_path}")
        
        # Verify checksum file exists
        checksum_path = output_path.with_suffix(output_path.suffix + ".sha256")
        if checksum_path.exists():
            logger.info(f"Checksum file generated: {checksum_path}")
            logger.info("Self-test PASSED.")
        else:
            logger.error("Checksum file was NOT generated.")
            raise RuntimeError("Checksum generation failed.")

    except Exception as e:
        logger.error(f"Self-test FAILED: {e}")
        raise


if __name__ == "__main__":
    main()