"""
Contract test for downloaded metadata schema (US1).

This test verifies that the metadata file produced by the data acquisition
pipeline adheres to the expected schema defined in the project contracts.

It loads `data/raw/metadata.json` (or the path specified in config) and validates:
1. Top-level structure (list of subject objects).
2. Presence of required fields: 'participant_id', 'dream_recall_frequency'.
3. Data types for critical fields.
4. Absence of nulls in required fields.

This test is designed to FAIL if the metadata file is missing, malformed,
or if the schema drifts from the specification.
"""
import json
import os
import pytest
from pathlib import Path

# Import config to get dynamic paths if needed, though we use defaults here
try:
    from utils.config import get_config_summary
except ImportError:
    # Fallback for direct execution outside package context if necessary
    # In CI, this should resolve correctly
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.config import get_config_summary


# Expected schema definition
REQUIRED_FIELDS = ["participant_id", "dream_recall_frequency"]
OPTIONAL_FIELDS = ["age", "sex", "hand"]  # Common fMRI metadata fields
REQUIRED_TYPES = {
    "participant_id": (str, int),
    "dream_recall_frequency": (int, float)
}


def load_metadata_file():
    """
    Loads the metadata JSON file from the standard data location.
    Raises FileNotFoundError if the file does not exist.
    """
    # Determine the data root. Usually 'data' relative to project root.
    # We assume the test runs from the project root or the path is absolute.
    project_root = Path(__file__).parent.parent.parent
    metadata_path = project_root / "data" / "raw" / "metadata.json"

    if not metadata_path.exists():
        # Allow the test to fail gracefully with a clear message if data hasn't been downloaded yet
        # This is expected in a fresh environment before T014/T016 runs
        raise FileNotFoundError(
            f"Metadata file not found at {metadata_path}. "
            "Ensure T014 (validate_metadata) and T016 (download) have been executed."
        )

    with open(metadata_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Metadata root must be a list of subject objects.")

    return data


def test_metadata_schema_structure():
    """
    Contract Test: Verify the top-level structure of the metadata.
    """
    data = load_metadata_file()

    assert isinstance(data, list), "Metadata must be a list of subjects."
    assert len(data) > 0, "Metadata list cannot be empty."


def test_metadata_required_fields():
    """
    Contract Test: Verify all required fields exist in every subject record.
    """
    data = load_metadata_file()

    for idx, subject in enumerate(data):
        assert isinstance(subject, dict), f"Subject {idx} is not a dictionary."

        for field in REQUIRED_FIELDS:
            assert field in subject, (
                f"Missing required field '{field}' in subject {idx} "
                f"(participant_id: {subject.get('participant_id', 'UNKNOWN')})."
            )


def test_metadata_field_types():
    """
    Contract Test: Verify data types for critical fields.
    """
    data = load_metadata_file()

    for idx, subject in enumerate(data):
        for field, expected_types in REQUIRED_TYPES.items():
            if field in subject:
                value = subject[field]
                assert isinstance(value, expected_types), (
                    f"Field '{field}' in subject {idx} has invalid type "
                    f"{type(value).__name__}. Expected one of {expected_types}."
                )


def test_metadata_no_nulls_in_required():
    """
    Contract Test: Ensure required fields are not null/None.
    """
    data = load_metadata_file()

    for idx, subject in enumerate(data):
        for field in REQUIRED_FIELDS:
            value = subject.get(field)
            assert value is not None, (
                f"Field '{field}' is null in subject {idx}."
            )
            # Also check for empty string if applicable
            if isinstance(value, str):
                assert len(value.strip()) > 0, (
                    f"Field '{field}' is empty string in subject {idx}."
                )


def test_metadata_dream_recall_frequency_validity():
    """
    Contract Test: Verify dream_recall_frequency is within plausible bounds.
    Assuming a scale (e.g., 1-5 or 0-100), we check for non-negative values.
    Adjust bounds if the specific OpenNeuro dataset uses a different scale.
    """
    data = load_metadata_file()

    for idx, subject in enumerate(data):
        drf = subject.get("dream_recall_frequency")
        if drf is not None:
            # Basic sanity check: usually a frequency or score >= 0
            assert drf >= 0, (
                f"dream_recall_frequency in subject {idx} is negative ({drf})."
            )
            # If it's a frequency count, it should be an integer or float.
            # If it's a scale (1-5), we might want to check upper bound.
            # For now, we just ensure it's a number.

if __name__ == "__main__":
    pytest.main([__file__, "-v"])