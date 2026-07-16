from typing import Dict, Any, List, Optional
from datetime import datetime
import re
from utils.logger import get_logger

logger = get_logger(__name__)

class DataValidator:
    """
    Validates incoming session data against the schema defined in contracts/session.schema.yaml.
    Ensures strict adherence to FR-006 and EC-001 requirements.
    """

    def __init__(self):
        self.required_fields = [
            "participant_id",
            "disability_type",
            "interface_type",
            "sequence",
            "start_time",
            "end_time",
            "error_count",
            "explanation_engagement_time_seconds",
            "sus_score",
            "status"
        ]
        
        self.status_values = ["complete", "incomplete"]
        self.disability_types = [
            "visual_impairment", 
            "hearing_impairment", 
            "motor_impairment", 
            "cognitive_impairment", 
            "none"
        ]

    def validate_session_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates a session dictionary.
        
        Returns:
            Dict with keys:
                - valid (bool)
                - errors (List[str])
        """
        errors = []
        
        # 1. Check required fields
        for field in self.required_fields:
            if field not in data or data[field] is None:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return {"valid": False, "errors": errors}

        # 2. Validate 'status'
        if data["status"] not in self.status_values:
            errors.append(f"Invalid status value: {data['status']}. Must be one of {self.status_values}")

        # 3. Validate 'disability_type'
        if data["disability_type"] not in self.disability_types:
            # Log warning but maybe not fail if we want to be flexible, 
            # but strict validation per spec suggests we should catch unknowns.
            logger.warning(f"Unknown disability_type encountered: {data['disability_type']}")
            # For strictness, we treat unknown as invalid per EC-001
            errors.append(f"Invalid disability_type: {data['disability_type']}")

        # 4. Validate 'sequence' is a list
        if not isinstance(data["sequence"], list):
            errors.append("Sequence must be a list of interface types")

        # 5. Validate numeric fields
        numeric_fields = ["error_count", "explanation_engagement_time_seconds", "sus_score"]
        for field in numeric_fields:
            val = data.get(field)
            if val is not None:
                try:
                    float(val)
                    if field == "error_count" and val < 0:
                        errors.append(f"{field} cannot be negative")
                    if field == "explanation_engagement_time_seconds" and val < 0:
                        errors.append(f"{field} cannot be negative")
                except (ValueError, TypeError):
                    errors.append(f"{field} must be numeric")

        # 6. Validate SUS Score range (0-100) if present and complete
        if data["status"] == "complete" and data.get("sus_score") is not None:
            if not (0 <= data["sus_score"] <= 100):
                errors.append(f"SUS score must be between 0 and 100, got {data['sus_score']}")

        # 7. Validate dropout_reason presence based on status
        if data["status"] == "incomplete" and not data.get("dropout_reason"):
            errors.append("dropout_reason is required for incomplete sessions")

        # 8. Validate timestamps
        for time_field in ["start_time", "end_time"]:
            val = data.get(time_field)
            if val:
                try:
                    # Handle ISO string or datetime object
                    if isinstance(val, str):
                        datetime.fromisoformat(val.replace('Z', '+00:00'))
                    elif isinstance(val, datetime):
                        pass
                    else:
                        errors.append(f"{time_field} must be a valid datetime or ISO string")
                except ValueError:
                    errors.append(f"Invalid datetime format for {time_field}")

        # 9. Ensure end_time >= start_time
        start = data.get("start_time")
        end = data.get("end_time")
        if start and end:
            if isinstance(start, str):
                start = datetime.fromisoformat(start.replace('Z', '+00:00'))
            if isinstance(end, str):
                end = datetime.fromisoformat(end.replace('Z', '+00:00'))
            
            if end < start:
                errors.append("end_time cannot be before start_time")

        is_valid = len(errors) == 0
        if not is_valid:
            logger.warning(f"Validation failed for session {data.get('session_id', 'unknown')}: {errors}")
        
        return {"valid": is_valid, "errors": errors}

    def validate_schema_file(self, schema_path: str) -> bool:
        """
        Placeholder for loading and validating against a YAML schema file if needed.
        Currently, validation is hardcoded based on the schema definition.
        """
        logger.info(f"Schema validation logic is currently hardcoded. Checking {schema_path} existence...")
        import os
        return os.path.exists(schema_path)

def main():
    """
    CLI entry point for testing the validator.
    """
    logger.info("Testing DataValidator...")
    validator = DataValidator()
    
    # Test valid data
    valid_data = {
        "participant_id": "p-001",
        "disability_type": "visual_impairment",
        "interface_type": "explainable",
        "sequence": ["Traditional", "Explainable"],
        "start_time": "2023-01-01T10:00:00",
        "end_time": "2023-01-01T10:15:00",
        "error_count": 1,
        "explanation_engagement_time_seconds": 120.5,
        "sus_score": 80.0,
        "status": "complete"
    }
    
    result = validator.validate_session_data(valid_data)
    logger.info(f"Valid data test: {result}")
    assert result["valid"], "Valid data should pass validation"
    
    # Test invalid data (missing field)
    invalid_data = valid_data.copy()
    del invalid_data["sus_score"]
    
    result = validator.validate_session_data(invalid_data)
    logger.info(f"Invalid data test: {result}")
    assert not result["valid"], "Invalid data should fail validation"
    
    logger.info("Validator tests passed.")

if __name__ == "__main__":
    main()
