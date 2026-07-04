import json
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from models.data_models import Session
from utils.checksum import generate_checksum_file
from utils.logger import get_logger
from config.settings import get_settings

logger = get_logger(__name__)

class RawDataLogger:
    """
    Handles writing raw session data to immutable JSON files and generating
    corresponding checksums for integrity verification.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.settings = get_settings()
        self.base_dir = data_dir or Path(self.settings.data_raw_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"RawDataLogger initialized with base directory: {self.base_dir}")

    def _generate_filename(self, session_id: str) -> str:
        """Generate the filename for the session log."""
        return f"session_{session_id}.json"

    def _serialize_session(self, session: Session) -> Dict[str, Any]:
        """
        Serialize a Session object to a dictionary suitable for JSON.
        Handles nested objects and datetime serialization.
        """
        data = {
            "session_id": session.session_id,
            "participant_id": session.participant_id,
            "interface_type": session.interface_type,
            "start_time": session.start_time.isoformat() if session.start_time else None,
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "error_count": session.error_count,
            "explanation_engagement_time_seconds": session.explanation_engagement_time_seconds,
            "sus_score": session.sus_score,
            "skip_count": session.skip_count,
            "status": session.status,
            "disability_type": session.disability_type,
            "interface_sequence": session.interface_sequence,
            "metrics": session.metrics,
            "timestamp_logged": datetime.utcnow().isoformat()
        }
        return data

    def log_session(self, session: Session) -> Path:
        """
        Writes the session data to a JSON file and generates a checksum.

        Args:
            session: The Session object to log.

        Returns:
            Path: The path to the created JSON file.
        """
        if not session.session_id:
            session.session_id = str(uuid.uuid4())
            logger.warning(f"Session ID was missing, generated: {session.session_id}")

        filename = self._generate_filename(session.session_id)
        file_path = self.base_dir / filename

        # Check if file already exists to prevent overwriting immutable data
        if file_path.exists():
            logger.warning(f"Session file already exists: {file_path}. Skipping write.")
            return file_path

        try:
            data = self._serialize_session(session)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully logged session {session.session_id} to {file_path}")

            # Generate checksum
            checksum_path = generate_checksum_file(file_path)
            logger.info(f"Generated checksum for {file_path} at {checksum_path}")

            return file_path

        except Exception as e:
            logger.error(f"Failed to log session {session.session_id}: {e}", exc_info=True)
            raise

    def log_raw_data(self, data: Dict[str, Any], filename: Optional[str] = None) -> Path:
        """
        Logs a raw dictionary of data to a JSON file with checksum.
        Useful for logging intermediate states or custom data structures not fully
        captured by the Session model.

        Args:
            data: Dictionary of data to log.
            filename: Optional filename. If None, uses 'raw_data_{timestamp}.json'.

        Returns:
            Path: The path to the created JSON file.
        """
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"raw_data_{timestamp}.json"
        
        file_path = self.base_dir / filename

        if file_path.exists():
            logger.warning(f"Raw data file already exists: {file_path}. Skipping write.")
            return file_path

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully logged raw data to {file_path}")
            generate_checksum_file(file_path)
            return file_path

        except Exception as e:
            logger.error(f"Failed to log raw data: {e}", exc_info=True)
            raise

def main():
    """
    Entry point for testing the RawDataLogger independently.
    Creates a mock Session and logs it to verify the workflow.
    """
    from simulator.counterbalance import LatinSquareCounterbalancer
    from utils.seed import set_seed

    set_seed(42)
    
    logger.info("Starting RawDataLogger test...")
    
    # Initialize logger
    raw_logger = RawDataLogger()
    
    # Create a mock session
    session = Session(
        session_id="test_session_001",
        participant_id="P001",
        interface_type="Explainable",
        start_time=datetime.now(),
        end_time=datetime.now(),
        error_count=1,
        explanation_engagement_time_seconds=15.5,
        sus_score=85.0,
        skip_count=0,
        status="complete",
        disability_type="visual_impairment",
        interface_sequence=["Traditional", "Explainable"],
        metrics={
            "completion_time": 120.5,
            "accuracy": 0.95
        }
    )
    
    # Log the session
    try:
        file_path = raw_logger.log_session(session)
        print(f"Session logged successfully to: {file_path}")
        
        # Verify checksum file exists
        checksum_path = file_path.with_suffix(file_path.suffix + ".sha256")
        if checksum_path.exists():
            print(f"Checksum file generated: {checksum_path}")
        else:
            print("WARNING: Checksum file not found.")
            
    except Exception as e:
        print(f"Error during logging: {e}")
        raise

if __name__ == "__main__":
    main()