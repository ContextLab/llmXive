"""
Dataset metadata schema definition and validation for mindfulness training studies.

Defines the required structure for dataset metadata including pre/post scan counts,
intervention types, and scan parameters.
"""
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum


class InterventionType(Enum):
    """Supported mindfulness intervention types."""
    MBSR = "MBSR"
    MBCT = "MBCT"
    MEDITATION = "MEDITATION"
    MINDFULNESS_BASED = "MINDFULNESS_BASED"
    OTHER = "OTHER"


class ScanType(Enum):
    """Supported scan types for the study."""
    RESTING_STATE = "resting_state"
    TASK_BASED = "task_based"
    TASK_RESTING = "task_and_resting"


@dataclass
class DatasetMetadata:
    """
    Schema for dataset metadata.

    Required fields:
    - pre_scan_count: Number of scans before intervention
    - post_scan_count: Number of scans after intervention
    - intervention_type: Type of mindfulness intervention
    - scan_type: Type of fMRI scan collected
    """
    pre_scan_count: int
    post_scan_count: int
    intervention_type: str
    scan_type: str
    dataset_id: Optional[str] = None
    dataset_name: Optional[str] = None
    openneuro_url: Optional[str] = None
    notes: Optional[str] = None

    def __post_init__(self):
        """Validate required fields and types."""
        self._validate_intervention_type()
        self._validate_scan_type()
        self._validate_scan_counts()

    def _validate_intervention_type(self):
        """Ensure intervention_type is a valid string."""
        valid_types = [e.value for e in InterventionType]
        if self.intervention_type not in valid_types:
            raise ValueError(
                f"Invalid intervention_type: '{self.intervention_type}'. "
                f"Must be one of: {valid_types}"
            )

    def _validate_scan_type(self):
        """Ensure scan_type is a valid string."""
        valid_types = [e.value for e in ScanType]
        if self.scan_type not in valid_types:
            raise ValueError(
                f"Invalid scan_type: '{self.scan_type}'. "
                f"Must be one of: {valid_types}"
            )

    def _validate_scan_counts(self):
        """Ensure scan counts are non-negative integers."""
        if self.pre_scan_count < 0:
            raise ValueError(f"pre_scan_count must be >= 0, got {self.pre_scan_count}")
        if self.post_scan_count < 0:
            raise ValueError(f"post_scan_count must be >= 0, got {self.post_scan_count}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatasetMetadata":
        """Create instance from dictionary."""
        return cls(
            pre_scan_count=data["pre_scan_count"],
            post_scan_count=data["post_scan_count"],
            intervention_type=data["intervention_type"],
            scan_type=data["scan_type"],
            dataset_id=data.get("dataset_id"),
            dataset_name=data.get("dataset_name"),
            openneuro_url=data.get("openneuro_url"),
            notes=data.get("notes")
        )

    @classmethod
    def from_json(cls, json_str: str) -> "DatasetMetadata":
        """Create instance from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


def validate_schema(data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate a dictionary against the DatasetMetadata schema.

    Args:
        data: Dictionary to validate

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors: List[str] = []
    required_fields = ["pre_scan_count", "post_scan_count", "intervention_type", "scan_type"]

    # Check required fields
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    if errors:
        return False, errors

    # Validate types
    if not isinstance(data["pre_scan_count"], int):
        errors.append("pre_scan_count must be an integer")
    elif data["pre_scan_count"] < 0:
        errors.append("pre_scan_count must be non-negative")

    if not isinstance(data["post_scan_count"], int):
        errors.append("post_scan_count must be an integer")
    elif data["post_scan_count"] < 0:
        errors.append("post_scan_count must be non-negative")

    if not isinstance(data["intervention_type"], str):
        errors.append("intervention_type must be a string")
    else:
        valid_types = [e.value for e in InterventionType]
        if data["intervention_type"] not in valid_types:
            errors.append(
                f"intervention_type must be one of {valid_types}, "
                f"got '{data['intervention_type']}'"
            )

    if not isinstance(data["scan_type"], str):
        errors.append("scan_type must be a string")
    else:
        valid_types = [e.value for e in ScanType]
        if data["scan_type"] not in valid_types:
            errors.append(
                f"scan_type must be one of {valid_types}, "
                f"got '{data['scan_type']}'"
            )

    return len(errors) == 0, errors


def create_sample_metadata() -> Dict[str, Any]:
    """
    Create a sample metadata dictionary for testing.

    Returns:
        Dictionary with valid sample metadata
    """
    return {
        "dataset_id": "ds000001",
        "dataset_name": "Sample Mindfulness Study",
        "pre_scan_count": 10,
        "post_scan_count": 10,
        "intervention_type": "MBSR",
        "scan_type": "resting_state",
        "openneuro_url": "https://openneuro.org/datasets/ds000001",
        "notes": "Sample dataset for testing schema validation"
    }


def validate_sample_json(json_str: str) -> tuple[bool, List[str]]:
    """
    Validate a JSON string against the schema.

    Args:
        json_str: JSON string to validate

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    try:
        data = json.loads(json_str)
        return validate_schema(data)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {str(e)}"]


def main():
    """Run validation tests on sample metadata."""
    print("Testing DatasetMetadata schema...")

    # Test 1: Create sample metadata
    sample = create_sample_metadata()
    print(f"Sample metadata: {json.dumps(sample, indent=2)}")

    # Test 2: Validate sample
    is_valid, errors = validate_schema(sample)
    if is_valid:
        print("✓ Sample metadata is valid")
    else:
        print(f"✗ Sample metadata validation failed: {errors}")
        return 1

    # Test 3: Validate JSON string
    json_str = json.dumps(sample)
    is_valid, errors = validate_sample_json(json_str)
    if is_valid:
        print("✓ JSON validation passed")
    else:
        print(f"✗ JSON validation failed: {errors}")
        return 1

    # Test 4: Test invalid data
    invalid_data = {
        "pre_scan_count": -1,
        "post_scan_count": 10,
        "intervention_type": "INVALID_TYPE",
        "scan_type": "resting_state"
    }
    is_valid, errors = validate_schema(invalid_data)
    if not is_valid:
        print(f"✓ Correctly rejected invalid data: {errors}")
    else:
        print("✗ Failed to reject invalid data")
        return 1

    # Test 5: Test missing required field
    missing_field = {
        "pre_scan_count": 10,
        "post_scan_count": 10,
        "intervention_type": "MBSR"
        # scan_type missing
    }
    is_valid, errors = validate_schema(missing_field)
    if not is_valid and "scan_type" in str(errors):
        print(f"✓ Correctly detected missing field: {errors}")
    else:
        print("✗ Failed to detect missing required field")
        return 1

    print("\n✓ All schema validation tests passed")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
