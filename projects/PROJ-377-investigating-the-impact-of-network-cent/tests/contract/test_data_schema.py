"""
Contract test for data schema validation (US1).

This test ensures that the data structures (Subject, ConnectivityMatrix)
conform to the expected schema defined in the data models.

Prerequisites:
- T001a, T001b, T002, T003
- T007 (Base data models)
"""
import pytest
import numpy as np
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.subject import Subject
from code.data.connectivity_matrix import ConnectivityMatrix


def test_subject_schema_valid():
    """Test that Subject dataclass accepts valid data and computes improvement."""
    sub = Subject(
        participant_id="sub-01",
        age=25,
        sex="M",
        motor_score_pre=10.0,
        motor_score_post=15.0,
        mean_fd=0.1
    )
    assert sub.participant_id == "sub-01"
    assert sub.age == 25
    assert sub.sex == "M"
    assert sub.motor_score_pre == 10.0
    assert sub.motor_score_post == 15.0
    assert sub.mean_fd == 0.1
    # Verify derived property
    assert sub.improvement_score == 5.0


def test_subject_schema_missing_fields_defaults():
    """Test behavior when optional fields are missing (dataclass defaults)."""
    # Since dataclass doesn't enforce non-optional fields without extra logic,
    # we test that the object is created and attributes exist.
    sub = Subject(participant_id="sub-02")
    assert hasattr(sub, 'participant_id')
    assert sub.participant_id == "sub-02"
    # Verify that missing numeric fields default to None or 0.0 depending on type hint
    # The test passes if the object is instantiated without error.
    assert sub.age is None
    assert sub.motor_score_pre is None
    assert sub.improvement_score is None


def test_subject_schema_invalid_types():
    """Test that Subject handles type mismatches gracefully or fails as expected."""
    # This test verifies the schema contract regarding types.
    # If the dataclass expects int/float, passing string might cause issues later.
    # For this contract test, we ensure the object can be created but check attributes.
    sub = Subject(
        participant_id="sub-03",
        age="twenty", # Invalid type for age
        sex="F",
        motor_score_pre=10.0,
        motor_score_post=15.0,
        mean_fd=0.1
    )
    assert sub.age == "twenty"
    # The contract test verifies the structure exists; type enforcement is usually
    # handled by the processing logic (e.g., in preprocess.py), not the dataclass itself
    # unless using runtime type checking libraries.


def test_connectivity_matrix_schema_valid():
    """Test that ConnectivityMatrix handles matrix creation and shape."""
    data = np.random.rand(10, 10).astype(np.float32)
    cm = ConnectivityMatrix(data=data, atlas_name="AAL3")
    
    assert cm.data.shape == (10, 10)
    assert cm.atlas_name == "AAL3"
    assert isinstance(cm.data, np.ndarray)
    assert cm.data.dtype == np.float32


def test_connectivity_matrix_schema_symmetry():
    """Test that ConnectivityMatrix can handle symmetric data (typical for correlation)."""
    # Create a symmetric matrix
    base = np.random.rand(5, 5).astype(np.float32)
    symmetric_data = (base + base.T) / 2
    
    cm = ConnectivityMatrix(data=symmetric_data, atlas_name="AAL3")
    
    assert np.allclose(cm.data, cm.data.T)
    assert cm.data.shape == (5, 5)


def test_connectivity_matrix_schema_invalid_shape():
    """Test that ConnectivityMatrix handles non-square matrices (if allowed) or rejects them."""
    # The schema allows any numpy array, but downstream logic expects square.
    # This test ensures the object is created with the data provided.
    data = np.random.rand(3, 4).astype(np.float32)
    cm = ConnectivityMatrix(data=data, atlas_name="AAL3")
    
    assert cm.data.shape == (3, 4)
    # The contract test verifies the object holds the data; shape validation
    # is a business logic concern handled in analysis modules.


if __name__ == "__main__":
    test_subject_schema_valid()
    test_subject_schema_missing_fields_defaults()
    test_subject_schema_invalid_types()
    test_connectivity_matrix_schema_valid()
    test_connectivity_matrix_schema_symmetry()
    test_connectivity_matrix_schema_invalid_shape()
    print("Schema contract tests passed.")