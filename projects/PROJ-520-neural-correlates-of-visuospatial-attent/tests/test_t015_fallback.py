import os
import json
import pytest
from pathlib import Path
import numpy as np
from unittest.mock import patch, MagicMock

# Import the function we are testing
# Assuming the file is code/preprocessing.py
# We need to adjust the import path based on the project structure
# Since we are in tests/, we might need to add code/ to sys.path or import as code.preprocessing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from preprocessing import fallback_to_landmark_timestamps, update_metadata_with_fallback

@pytest.fixture
def mock_raw_data():
    """Create a mock MNE Raw object with annotations."""
    raw = MagicMock()
    # Mock annotations
    raw.annotations = MagicMock()
    # Create some mock annotations: (onset, duration, description)
    # Active event at 1.0s, Passive at 2.0s, Active at 3.0s
    raw.annotations.onset = np.array([1.0, 2.0, 3.0])
    raw.annotations.duration = np.array([0.1, 0.1, 0.1])
    raw.annotations.description = np.array(["active", "passive", "active"])
    return raw

@pytest.fixture
def temp_metadata_path(tmp_path):
    return tmp_path / "metadata.json"

def test_fallback_to_landmark_timestamps_success(mock_raw_data):
    """Test that fallback successfully reconstructs events from annotations."""
    events = None # Simulate missing events
    sample_rate = 1000.0
    
    new_events, success = fallback_to_landmark_timestamps(
        events, mock_raw_data, sample_rate
    )
    
    assert success is True
    assert len(new_events) == 3
    # Check that events are at the correct sample indices
    # 1.0s * 1000 = 1000, 2.0s * 1000 = 2000, etc.
    assert new_events[0][0] == 1000
    assert new_events[1][0] == 2000
    assert new_events[2][0] == 3000
    
    # Check event IDs (simplified mapping in the function)
    # active -> 1, passive -> 2
    assert new_events[0][2] == 1
    assert new_events[1][2] == 2
    assert new_events[2][2] == 1

def test_fallback_to_landmark_timestamps_no_landmarks(mock_raw_data):
    """Test fallback when no landmark events are found."""
    # Modify mock to have no matching landmarks
    mock_raw_data.annotations.description = np.array(["noise", "artifact", "other"])
    
    events = None
    sample_rate = 1000.0
    
    with pytest.raises(RuntimeError, match="Unable to reconstruct events"):
        fallback_to_landmark_timestamps(events, mock_raw_data, sample_rate)

def test_update_metadata_with_fallback_true(temp_metadata_path):
    """Test that metadata is updated correctly when fallback is applied."""
    condition_counts = {"active": 10, "passive": 10}
    
    update_metadata_with_fallback(temp_metadata_path, condition_counts, fallback_applied=True)
    
    assert temp_metadata_path.exists()
    with open(temp_metadata_path, 'r') as f:
        data = json.load(f)
    
    assert "assumptions" in data
    assert data["assumptions"]["event_source"] == "landmark_fallback"
    assert "fallback_details" in data["assumptions"]
    assert data["validation_results"]["counts"] == condition_counts

def test_update_metadata_with_fallback_false(temp_metadata_path):
    """Test that metadata is updated correctly when fallback is NOT applied."""
    condition_counts = {"active": 10, "passive": 10}
    
    update_metadata_with_fallback(temp_metadata_path, condition_counts, fallback_applied=False)
    
    assert temp_metadata_path.exists()
    with open(temp_metadata_path, 'r') as f:
        data = json.load(f)
    
    assert "assumptions" in data
    assert data["assumptions"]["event_source"] == "standard_markers"
    assert "fallback_details" not in data["assumptions"]
    assert data["validation_results"]["counts"] == condition_counts
