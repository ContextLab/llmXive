import json
import hashlib
import uuid
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import yaml

from utils.logger import get_logger

logger = get_logger(__name__)

class RawDataLogger:
    """
    Handles logging of raw session data to JSON files under data/raw/.
    Ensures the logged data conforms to the session schema and includes
    explanation_engagement_time_seconds as required by T016b.
    """

    def __init__(self, schema_path: Optional[str] = None):
        self.schema_path = schema_path or "contracts/session.schema.yaml"
        self.schema = self.load_schema()
        self.output_dir = Path("data/raw")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_schema(self) -> Dict[str, Any]:
        """Load the JSON schema from the contracts directory."""
        if not os.path.exists(self.schema_path):
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
        
        with open(self.schema_path, 'r') as f:
            return yaml.safe_load(f)

    def validate_session_against_schema(self, session_data: Dict[str, Any]) -> bool:
        """
        Validates session data against the loaded schema.
        For T016b, this ensures 'explanation_engagement_time_seconds' is present.
        """
        # Basic manual validation for required fields since jsonschema might not be installed
        required_fields = [
            "participant_id", "disability_type", "interface_type", 
            "sequence", "start_time", "end_time", "error_count",
            "explanation_engagement_time_seconds", "sus_score", "status"
        ]
        
        missing = [f for f in required_fields if f not in session_data]
        if missing:
            logger.error(f"Session data missing required fields: {missing}")
            return False
        
        # Specific check for T016b
        if not isinstance(session_data.get("explanation_engagement_time_seconds"), (int, float)):
            logger.error("explanation_engagement_time_seconds must be a number.")
            return False

        return True

    def log_session(self, session_data: Dict[str, Any]) -> str:
        """
        Logs a session to a JSON file.
        Returns the path to the created file.
        """
        if not self.validate_session_against_schema(session_data):
            raise ValueError("Session data failed schema validation.")

        session_id = str(uuid.uuid4())
        filename = f"session_{session_id}.json"
        filepath = self.output_dir / filename

        # Ensure timestamps are strings
        session_data["start_time"] = session_data.get("start_time") or datetime.now().isoformat()
        session_data["end_time"] = session_data.get("end_time") or datetime.now().isoformat()
        session_data["session_id"] = session_id

        with open(filepath, 'w') as f:
            json.dump(session_data, f, indent=2)

        logger.info(f"Session logged to {filepath}")
        return str(filepath)

def main():
    """
    CLI entry point to demonstrate raw data logging with explanation_engagement_time_seconds.
    """
    logger = get_logger(__name__)
    logger.info("Testing RawDataLogger with T016b requirements...")

    logger_instance = RawDataLogger()
    
    # Construct a valid session payload
    test_session = {
        "participant_id": "P001",
        "disability_type": "visual_impairment",
        "interface_type": "explainable",
        "sequence": "explainable_traditional",
        "start_time": datetime.now().isoformat(),
        "end_time": datetime.now().isoformat(),
        "error_count": 1,
        "explanation_engagement_time_seconds": 15.5,  # T016b Requirement
        "sus_score": 85,
        "status": "complete"
    }

    try:
        path = logger_instance.log_session(test_session)
        print(f"SUCCESS: Session logged to {path}")
        
        # Verify content
        with open(path, 'r') as f:
            content = json.load(f)
            assert "explanation_engagement_time_seconds" in content
            print(f"Verified: explanation_engagement_time_seconds = {content['explanation_engagement_time_seconds']}")
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()