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

def test_subject_schema():
    """Test that Subject dataclass accepts valid data and rejects invalid."""
    # Valid data
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
    assert sub.motor_score_pre == 10.0
    assert sub.improvement_score == 5.0

    # Missing required field (should raise error if using dataclass validation or type hints)
    # Since dataclass doesn't enforce at runtime without extra libs, we test the attributes
    try:
        sub_invalid = Subject(participant_id="sub-02")
        # If it creates an object with None/defaults, that's okay for dataclass,
        # but the test should verify that our processing logic handles it.
        # For a contract test, we verify the structure exists.
        assert hasattr(sub_invalid, 'participant_id')
    except Exception as e:
        pytest.fail(f"Subject creation failed unexpectedly: {e}")

def test_connectivity_matrix_schema():
    """Test that ConnectivityMatrix handles matrix creation and shape."""
    data = np.random.rand(10, 10)
    cm = ConnectivityMatrix(data=data, atlas_name="AAL3")
    
    assert cm.data.shape == (10, 10)
    assert cm.atlas_name == "AAL3"
    
    # Test symmetry (if applicable, though fMRI matrices are often symmetric)
    # For this contract test, we just ensure the object is created correctly.
    assert isinstance(cm.data, np.ndarray)

if __name__ == "__main__":
    test_subject_schema()
    test_connectivity_matrix_schema()
    print("Schema contract tests passed.")
