"""
Data Validation Module.

Validates session data against the schema.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import re
from utils.logger import get_logger

logger = get_logger(__name__)

class DataValidator:
    """
    Validates session data structure and content.
    """

    def __init__(self):
        self.required_fields = [
            "participant_id", "session_id", "interface_sequence",
            "start_time", "end_time", "status"
        ]

    def validate_session(self, data: Dict[str, Any]) -> bool:
        """
        Validate a session dictionary.

        Args:
            data: Session data dictionary.

        Returns:
            True if valid, False otherwise.
        """
        for field in self.required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate participant_id format (alphanumeric)
        if not re.match(r"^[a-zA-Z0-9_-]+$", data["participant_id"]):
            logger.error(f"Invalid participant_id format: {data['participant_id']}")
            return False

        # Validate status
        if data["status"] not in ["complete", "incomplete"]:
            logger.error(f"Invalid status: {data['status']}")
            return False

        return True

def main():
    """Test the validator."""
    validator = DataValidator()
    valid_data = {
        "participant_id": "P001",
        "session_id": "s1",
        "interface_sequence": ["traditional", "explainable"],
        "start_time": "2023-01-01T00:00:00",
        "end_time": "2023-01-01T00:10:00",
        "status": "complete"
    }
    print(f"Valid: {validator.validate_session(valid_data)}")

if __name__ == "__main__":
    main()
