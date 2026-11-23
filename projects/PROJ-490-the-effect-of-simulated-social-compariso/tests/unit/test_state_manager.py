"""
Unit tests for the state manager module.
"""
import os
import yaml
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from data.state_manager import load_state_file, save_state_file, update_project_state, update_data_source_type
from data.config import get_config, reset_config


@pytest.fixture
def temp_state_dir(tmp_path):
    """Create a temporary state directory."""
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    return state_dir


@pytest.fixture
def mock_config(temp_state_dir):
    """Mock config to use temporary state directory."""
    mock_config = {
        'state_dir': str(temp_state_dir),
        'raw_dir': str(temp_state_dir / "raw"),
        'processed_dir': str(temp_state_dir / "processed"),
        'log_dir': str(temp_state_dir / "logs")
    }
    with patch('data.config.get_config', return_value=mock_config):
        yield mock_config


def test_load_state_file_not_found(mock_config, temp_state_dir):
    """Test loading a non-existent state file returns empty dict."""
    state_path = temp_state_dir / "nonexistent.yaml"
    result = load_state_file(state_path)
    assert result == {}


def test_load_state_file_exists(mock_config, temp_state_dir):
    """Test loading an existing state file."""
    state_path = temp_state_dir / "test.yaml"
    data = {'key': 'value', 'number': 123}
    with open(state_path, 'w') as f:
        yaml.dump(data, f)

    result = load_state_file(state_path)
    assert result == data


def test_save_state_file(mock_config, temp_state_dir):
    """Test saving a state file."""
    state_path = temp_state_dir / "new_state.yaml"
    data = {'new_key': 'new_value'}
    save_state_file(state_path, data)

    assert state_path.exists()
    with open(state_path, 'r') as f:
        loaded = yaml.safe_load(f)
    assert loaded == data


def test_update_project_state(mock_config, temp_state_dir):
    """Test updating project state merges correctly."""
    project_id = "TEST-PROJ"
    state_file = temp_state_dir / f"{project_id}.yaml"

    # Create initial state
    initial_data = {'existing_key': 'existing_value'}
    save_state_file(state_file, initial_data)

    # Update
    update_project_state(project_id, {'new_key': 'new_value'})

    # Verify
    with open(state_file, 'r') as f:
        final_data = yaml.safe_load(f)

    assert final_data['existing_key'] == 'existing_value'
    assert final_data['new_key'] == 'new_value'


def test_update_data_source_type_valid(mock_config, temp_state_dir):
    """Test updating data_source_type with valid values."""
    project_id = "TEST-PROJ"

    update_data_source_type(project_id, 'real')
    state_file = temp_state_dir / f"{project_id}.yaml"
    with open(state_file, 'r') as f:
        data = yaml.safe_load(f)
    assert data['data_source_type'] == 'real'

    update_data_source_type(project_id, 'synthetic')
    with open(state_file, 'r') as f:
        data = yaml.safe_load(f)
    assert data['data_source_type'] == 'synthetic'


def test_update_data_source_type_invalid(mock_config, temp_state_dir):
    """Test updating data_source_type with invalid value raises error."""
    project_id = "TEST-PROJ"

    with pytest.raises(ValueError, match="Invalid data_source_type"):
        update_data_source_type(project_id, 'invalid_type')