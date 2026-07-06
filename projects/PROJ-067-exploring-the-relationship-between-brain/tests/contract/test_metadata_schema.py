"""
Contract test for downloaded metadata schema (T011).
Validates that the metadata fetched from OpenNeuro matches the expected schema.
"""
import pytest
from typing import Dict, Any, List

# Mock data to simulate the response from T014 fetch
SAMPLE_OPENNEURO_METADATA = {
    "participants": [
        {
            "participant_id": "sub-01",
            "age": 24,
            "sex": "M",
            "dream_recall_frequency": 5.0,
            "hand": "right"
        },
        {
            "participant_id": "sub-02",
            "age": 30,
            "sex": "F",
            "dream_recall_frequency": 12.0,
            "hand": "left"
        },
        {
            "participant_id": "sub-03",
            "age": 22,
            "sex": "M",
            # Missing dream_recall_frequency intentionally for schema test
            "hand": "right"
        }
    ]
}

REQUIRED_FIELDS = [
    "participant_id",
    "dream_recall_frequency"
]

def validate_participant_schema(participant: Dict[str, Any]) -> List[str]:
    """
    Validates a single participant record against the schema.
    Returns a list of missing required fields.
    """
    missing = []
    for field in REQUIRED_FIELDS:
        if field not in participant or participant[field] is None:
            missing.append(field)
    return missing

def test_schema_has_required_fields():
    """Test that all participants in the sample have required fields."""
    for p in SAMPLE_OPENNEURO_METADATA["participants"]:
        missing = validate_participant_schema(p)
        # sub-03 is expected to fail, others should pass
        if p["participant_id"] == "sub-03":
            assert "dream_recall_frequency" in missing
        else:
            assert len(missing) == 0, f"Unexpected missing fields for {p['participant_id']}: {missing}"

def test_schema_validation_logic():
    """Test the validation logic itself."""
    valid_record = {"participant_id": "sub-99", "dream_recall_frequency": 10}
    invalid_record = {"participant_id": "sub-98"}
    
    assert validate_participant_schema(valid_record) == []
    assert "dream_recall_frequency" in validate_participant_schema(invalid_record)
