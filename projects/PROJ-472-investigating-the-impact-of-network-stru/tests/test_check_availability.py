"""
Unit tests for T011a: check_availability.py
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Mock config to use temp directory
@pytest.fixture
def temp_data_root():
    with tempfile.TemporaryDirectory() as tmpdir:
        processed_dir = Path(tmpdir) / "processed"
        processed_dir.mkdir()
        with patch('config.get_data_root', return_value=Path(tmpdir)):
            yield processed_dir

@pytest.fixture
def mock_logger():
    with patch('code.data.check_availability.get_logger') as mock:
        yield mock

def test_check_availability_real_data(temp_data_root, mock_logger):
    """Test case: routing_state indicates real data exists."""
    # Create mock routing_state.json
    routing_state = {
        "simulation_required": False,
        "path": "correlation",
        "N": 10,
        "N_MIN": 5
    }
    routing_path = temp_data_root / "routing_state.json"
    with open(routing_path, 'w') as f:
        json.dump(routing_state, f)

    # Import after patching config
    from code.data.check_availability import check_availability

    result = check_availability()

    assert result["has_real_data"] is True
    assert result["status"] == "real_data_available"
    assert "real_data_available" in result["message"]

    # Verify output file was created
    output_path = temp_data_root / "data_availability_status.json"
    assert output_path.exists()
    with open(output_path, 'r') as f:
        output_data = json.load(f)
    assert output_data["has_real_data"] is True

def test_check_availability_simulation_required(temp_data_root, mock_logger):
    """Test case: routing_state indicates simulation is required."""
    # Create mock routing_state.json
    routing_state = {
        "simulation_required": True,
        "path": "simulation",
        "N": 10,
        "N_MIN": 5
    }
    routing_path = temp_data_root / "routing_state.json"
    with open(routing_path, 'w') as f:
        json.dump(routing_state, f)

    from code.data.check_availability import check_availability

    result = check_availability()

    assert result["has_real_data"] is False
    assert result["status"] == "simulation_required"
    assert "simulation_required" in result["message"]

def test_check_availability_missing_file(temp_data_root, mock_logger):
    """Test case: routing_state.json does not exist."""
    # Ensure file does NOT exist
    routing_path = temp_data_root / "routing_state.json"
    assert not routing_path.exists()

    from code.data.check_availability import check_availability

    with pytest.raises(FileNotFoundError, match="Routing state file missing"):
        check_availability()

def test_check_availability_missing_flag(temp_data_root, mock_logger):
    """Test case: routing_state exists but lacks the flag (ambiguous)."""
    # Create mock routing_state.json without the flag
    routing_state = {
        "path": "unknown",
        "N": 10
    }
    routing_path = temp_data_root / "routing_state.json"
    with open(routing_path, 'w') as f:
        json.dump(routing_state, f)

    from code.data.check_availability import check_availability

    # Should default to simulation_required and log a warning
    result = check_availability()

    assert result["has_real_data"] is False
    assert result["status"] == "simulation_required"
    # Verify warning was logged
    mock_logger.return_value.warning.assert_called()