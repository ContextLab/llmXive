import json
from pathlib import Path
from datetime import datetime
from utils.logger import get_logger
from utils.checksum import generate_checksum_file
from config.settings import get_settings
from models.data_models import Session

class SessionLogger:
    def __init__(self):
        self.logger = get_logger("session_logger")
        self.settings = get_settings()

    def log_session(self, session_data: dict):
        """
        Logs session data to a JSON file in the raw data directory.
        
        Args:
            session_data (dict): Dictionary containing session information.
                                 Must include 'session_id' and 'interface_variant'.
        """
        # Ensure required fields
        if 'session_id' not in session_data:
            session_data['session_id'] = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if 'interface_variant' not in session_data:
            self.logger.warning("No interface_variant provided in session_data. Defaulting to 'unknown'.")
            session_data['interface_variant'] = 'unknown'
        
        # Add timestamp
        session_data['logged_at'] = datetime.now().isoformat()
        
        raw_dir = self.settings.data_raw_dir
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = raw_dir / f"session_{session_data['session_id']}.json"
        
        with open(file_path, 'w') as f:
            json.dump(session_data, f, indent=2, default=str)
        
        generate_checksum_file(file_path)
        self.logger.info(f"Logged session {session_data['session_id']} with interface_variant '{session_data['interface_variant']}' to {file_path}")
        return file_path

    def log_session_from_model(self, session: Session, interface_variant: str, additional_data: dict = None):
        """
        Logs a Session model instance to JSON, explicitly recording the interface_variant.
        
        Args:
            session (Session): The Session dataclass instance.
            interface_variant (str): Either 'Traditional' or 'Explainable'.
            additional_data (dict, optional): Additional fields to include in the log.
        
        Returns:
            Path: Path to the created JSON file.
        """
        session_dict = {
            "session_id": session.session_id,
            "participant_id": session.participant_id,
            "interface_type": session.interface_type,
            "start_time": session.start_time.isoformat() if isinstance(session.start_time, datetime) else str(session.start_time),
            "end_time": session.end_time.isoformat() if isinstance(session.end_time, datetime) else str(session.end_time) if session.end_time else None,
            "error_count": session.error_count,
            "explanation_engagement_time_seconds": session.explanation_engagement_time_seconds,
            "sus_score": session.sus_score,
            "skip_count": session.skip_count,
            "status": session.status,
            "interface_variant": interface_variant,  # Explicitly record the variant
        }
        
        if additional_data:
            session_dict.update(additional_data)
        
        return self.log_session(session_dict)

    def log_dropout(self, session_id: str, participant_id: str, dropout_reason: str, interface_variant: str = "unknown"):
        """
        Logs a partial session resulting from a participant dropout.
        
        This method handles the specific requirement to log 'dropout_reason' and 
        flag the session status as 'incomplete'.
        
        Args:
            session_id (str): Unique identifier for the session.
            participant_id (str): ID of the participant who dropped out.
            dropout_reason (str): The reason provided by the participant or inferred.
            interface_variant (str): The interface being used when dropout occurred.
        
        Returns:
            Path: Path to the created JSON file.
        """
        if not session_id:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        dropout_data = {
            "session_id": session_id,
            "participant_id": participant_id,
            "interface_variant": interface_variant,
            "status": "incomplete",
            "dropout_reason": dropout_reason,
            "logged_at": datetime.now().isoformat(),
            # Fields that might be partial or zero for incomplete sessions
            "interface_type": interface_variant, 
            "start_time": datetime.now().isoformat(),
            "end_time": datetime.now().isoformat(),
            "error_count": 0,
            "explanation_engagement_time_seconds": 0,
            "sus_score": None,
            "skip_count": 0
        }
        
        raw_dir = self.settings.data_raw_dir
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = raw_dir / f"session_{session_id}.json"
        
        with open(file_path, 'w') as f:
            json.dump(dropout_data, f, indent=2, default=str)
        
        generate_checksum_file(file_path)
        self.logger.info(f"Logged dropout for session {session_id} (Participant: {participant_id}). Reason: '{dropout_reason}'. Status set to 'incomplete'.")
        return file_path

def main():
    """
    Main entry point for testing the session logger.
    Simulates a session log entry and a dropout scenario to verify functionality.
    """
    logger = SessionLogger()
    
    # Test 1: Log a complete session
    print("Testing complete session logging...")
    mock_session = {
        "session_id": "test_001_complete",
        "participant_id": "P001",
        "interface_type": "Explainable",
        "start_time": datetime.now(),
        "end_time": datetime.now(),
        "error_count": 0,
        "explanation_engagement_time_seconds": 15.5,
        "sus_score": 85,
        "skip_count": 0,
        "status": "complete"
    }
    
    file_path = logger.log_session_from_model(
        session=Session(
            session_id=mock_session["session_id"],
            participant_id=mock_session["participant_id"],
            interface_type=mock_session["interface_type"],
            start_time=mock_session["start_time"],
            end_time=mock_session["end_time"],
            error_count=mock_session["error_count"],
            explanation_engagement_time_seconds=mock_session["explanation_engagement_time_seconds"],
            sus_score=mock_session["sus_score"],
            skip_count=mock_session["skip_count"],
            status=mock_session["status"]
        ),
        interface_variant="Explainable"
    )
    print(f"Complete session logged successfully to: {file_path}")
    
    # Test 2: Log a dropout scenario (T020 requirement)
    print("\nTesting dropout handling...")
    dropout_path = logger.log_dropout(
        session_id="test_002_dropout",
        participant_id="P002",
        dropout_reason="Participant requested to stop due to fatigue",
        interface_variant="Traditional"
    )
    print(f"Dropout session logged successfully to: {dropout_path}")
    
    # Verify dropout file content
    with open(dropout_path, 'r') as f:
        content = json.load(f)
        assert content['status'] == 'incomplete', "Dropout status should be 'incomplete'."
        assert content['dropout_reason'] == "Participant requested to stop due to fatigue", "Dropout reason not recorded correctly."
        print("Verification passed: Dropout handling is correctly implemented.")

if __name__ == "__main__":
    main()