"""
Session Logging Module.

Handles logging of session data to JSON files, including interface variant tracking
and dropout handling.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import hashlib
from utils.logger import get_logger

logger = get_logger(__name__)

class SessionLogger:
    """
    Logs session data to disk, ensuring all required fields including interface_variant are recorded.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        if output_dir is None:
            output_dir = Path(__file__).parent.parent.parent / "data" / "raw"
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def log_session(self, session_data: Dict[str, Any]) -> Path:
        """
        Log a session to a JSON file.

        Args:
            session_data: Dictionary containing session information.
                Must include 'interface_variant' (str) for the current interface used.

        Returns:
            Path to the created file.
        """
        session_id = session_data.get("session_id", str(datetime.now().timestamp()))
        filename = f"session_{session_id}.json"
        filepath = self.output_dir / filename

        # Validate required fields
        required_fields = ["participant_id", "interface_variant", "start_time", "end_time"]
        missing_fields = [f for f in required_fields if f not in session_data]
        if missing_fields:
            raise ValueError(f"Missing required fields for session logging: {missing_fields}")

        # Add metadata
        session_data["logged_at"] = datetime.now().isoformat()
        session_data["log_version"] = "1.0"
        
        # Ensure interface_variant is recorded correctly
        if "interface_variant" in session_data:
            logger.info(f"Recording interface_variant: {session_data['interface_variant']}")
        
        # Write to file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, default=str)

        logger.info(f"Session logged to {filepath}")
        return filepath

    def log_session_with_metrics(self, participant_id: str, interface_variant: str, 
                                 metrics: Dict[str, Any], session_id: Optional[str] = None) -> Path:
        """
        Convenience method to log a complete session with metrics.

        Args:
            participant_id: Unique identifier for the participant.
            interface_variant: The interface used ('traditional' or 'explainable').
            metrics: Dictionary of collected metrics (completion_time, errors, sus_score, etc.).
            session_id: Optional custom session ID.

        Returns:
            Path to the created file.
        """
        if session_id is None:
            session_id = f"sess_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(participant_id.encode()).hexdigest()[:8]}"

        session_data = {
            "session_id": session_id,
            "participant_id": participant_id,
            "interface_variant": interface_variant,
            "start_time": metrics.get("start_time", datetime.now().isoformat()),
            "end_time": metrics.get("end_time", datetime.now().isoformat()),
            "metrics": metrics,
            "status": metrics.get("status", "complete")
        }

        return self.log_session(session_data)

    def log_dropout(self, participant_id: str, interface_variant: str, 
                    dropout_reason: str, session_id: Optional[str] = None) -> Path:
        """
        Log a partial session (dropout) to a JSON file.
        
        This method sets the status to 'incomplete', records the reason for dropout,
        and ensures the session is properly marked for exclusion from statistical analysis
        (as per T021-exclude).

        Args:
            participant_id: Unique identifier for the participant.
            interface_variant: The interface used at the time of dropout.
            dropout_reason: A string explaining why the session was not completed
                            (e.g., "User requested to stop", "System error", "Time limit exceeded").
            session_id: Optional custom session ID.

        Returns:
            Path to the created file.
        """
        if session_id is None:
            session_id = f"sess_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(participant_id.encode()).hexdigest()[:8]}"

        session_data = {
            "session_id": session_id,
            "participant_id": participant_id,
            "interface_variant": interface_variant,
            "start_time": datetime.now().isoformat(),
            "end_time": datetime.now().isoformat(),
            "status": "incomplete",
            "dropout_reason": dropout_reason,
            "metrics": {}
        }

        logger.warning(f"Logging dropout for participant {participant_id}: {dropout_reason}")
        return self.log_session(session_data)

def main():
    """Test the session logger with interface variant tracking and dropout handling."""
    logger_instance = SessionLogger()
    
    # Test 1: Test data simulating a completed session
    test_metrics = {
        "completion_time_seconds": 120.5,
        "error_count": 2,
        "sus_score": 85,
        "explanation_engagement_time_seconds": 15.3,
        "start_time": datetime.now().isoformat(),
        "end_time": datetime.now().isoformat(),
        "status": "complete"
    }

    path = logger_instance.log_session_with_metrics(
        participant_id="P001",
        interface_variant="explainable",
        metrics=test_metrics
    )
    print(f"Logged completed session to: {path}")
    
    # Verify file contents
    with open(path, "r") as f:
        data = json.load(f)
        assert "interface_variant" in data, "interface_variant missing from logged session"
        assert data["interface_variant"] == "explainable", "Incorrect interface_variant recorded"
        assert data["status"] == "complete", "Status should be complete"
        print("Verification passed: Completed session correctly recorded.")

    # Test 2: Test dropout handling
    dropout_path = logger_instance.log_dropout(
        participant_id="P002",
        interface_variant="traditional",
        dropout_reason="User requested to stop after 2 minutes"
    )
    print(f"Logged dropout session to: {dropout_path}")

    # Verify dropout file contents
    with open(dropout_path, "r") as f:
        data = json.load(f)
        assert data["status"] == "incomplete", "Status should be incomplete for dropout"
        assert "dropout_reason" in data, "dropout_reason missing from logged session"
        assert data["dropout_reason"] == "User requested to stop after 2 minutes", "Incorrect dropout reason"
        print("Verification passed: Dropout session correctly recorded with status='incomplete'.")

if __name__ == "__main__":
    main()