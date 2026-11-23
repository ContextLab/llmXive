import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import json

# Import the function to test
from preprocessing import validate_sample_size, update_metadata_with_validation

def test_validate_sample_size_pass():
    """Test that validation passes when all conditions have >= 100 epochs."""
    # Create a mock epochs object
    mock_epochs = Mock()
    mock_epochs.metadata = MagicMock()
    mock_epochs.metadata.columns = ['condition']
    mock_epochs.metadata.value_counts.return_value.to_dict.return_value = {
        'active': 120,
        'passive': 150
    }
    mock_epochs.event_id = None
    mock_epochs.events = None

    can_proceed, msg, counts = validate_sample_size(mock_epochs, min_required=50, min_powered=100)

    assert can_proceed is True
    assert "passed" in msg.lower()
    assert counts['active'] == 120
    assert counts['passive'] == 150

def test_validate_sample_size_underpowered():
    """Test that validation flags underpowered study (50 <= count < 100)."""
    mock_epochs = Mock()
    mock_epochs.metadata = MagicMock()
    mock_epochs.metadata.columns = ['condition']
    mock_epochs.metadata.value_counts.return_value.to_dict.return_value = {
        'active': 80,
        'passive': 120
    }
    mock_epochs.event_id = None
    mock_epochs.events = None

    can_proceed, msg, counts = validate_sample_size(mock_epochs, min_required=50, min_powered=100)

    assert can_proceed is True
    assert "underpowered" in msg.lower()
    assert "WARNING" in msg

def test_validate_sample_size_halt():
    """Test that validation halts if any condition has < 50 epochs."""
    mock_epochs = Mock()
    mock_epochs.metadata = MagicMock()
    mock_epochs.metadata.columns = ['condition']
    mock_epochs.metadata.value_counts.return_value.to_dict.return_value = {
        'active': 40,
        'passive': 120
    }
    mock_epochs.event_id = None
    mock_epochs.events = None

    with pytest.raises(ValueError, match="CRITICAL"):
        validate_sample_size(mock_epochs, min_required=50, min_powered=100)

def test_validate_sample_size_fallback_to_event_id():
    """Test validation when metadata is missing, falling back to event_id."""
    mock_epochs = Mock()
    mock_epochs.metadata = None
    mock_epochs.event_id = {'active': 1, 'passive': 2}
    mock_epochs.events = np.array([
        [0, 0, 1],
        [100, 0, 1],
        [200, 0, 1],
        [300, 0, 2],
        [400, 0, 2]
    ])

    can_proceed, msg, counts = validate_sample_size(mock_epochs, min_required=50, min_powered=100)

    # Should fail because counts are low (3 and 2)
    # But the function should not crash and should return counts
    # The function logic in validate_sample_size handles this
    # Note: The mock above has 3 'active' and 2 'passive'
    # This will trigger the halt condition
    # We expect an error or a flag. The function raises ValueError if < min_required
    
    # Let's adjust the mock to have enough for min_required but not min_powered
    mock_epochs.events = np.array([
        [0, 0, 1], [100, 0, 1], [200, 0, 1], [300, 0, 1], [400, 0, 1], # 5 active
        [500, 0, 2], [600, 0, 2], [700, 0, 2], [800, 0, 2], [900, 0, 2] # 5 passive
    ])
    
    # Set min_required to 5, min_powered to 10
    can_proceed, msg, counts = validate_sample_size(mock_epochs, min_required=5, min_powered=10)
    
    assert can_proceed is True
    assert "underpowered" in msg.lower()
    assert counts[1] == 5
    assert counts[2] == 5

def test_update_metadata_with_validation(tmp_path):
    """Test that metadata file is updated correctly."""
    metadata_path = tmp_path / 'metadata.json'
    counts = {'active': 100, 'passive': 100}
    status = "Test passed"
    is_powered = True

    update_metadata_with_validation(metadata_path, counts, status, is_powered)

    assert metadata_path.exists()
    with open(metadata_path, 'r') as f:
        data = json.load(f)

    assert 'sample_size_validation' in data
    assert data['sample_size_validation']['counts_per_condition'] == counts
    assert data['sample_size_validation']['status_message'] == status
    assert data['sample_size_validation']['is_powered'] is True
