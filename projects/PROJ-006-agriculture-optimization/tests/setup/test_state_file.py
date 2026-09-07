"""
Test to verify the state file T002a exists and is valid.
"""
import os
import yaml
import pytest
from pathlib import Path

STATE_FILE_PATH = "state/projects/PROJ-006-agriculture-optimization.yaml"

def test_state_file_exists():
    """Assert the state file exists."""
    assert os.path.exists(STATE_FILE_PATH), f"State file missing at {STATE_FILE_PATH}"

def test_state_file_is_valid_yaml():
    """Assert the state file is valid YAML."""
    with open(STATE_FILE_PATH, 'r', encoding='utf-8') as f:
        try:
            data = yaml.safe_load(f)
            assert data is not None
        except yaml.YAMLError:
            pytest.fail("State file is not valid YAML")

def test_state_file_schema():
    """Assert the state file contains required keys and correct project_id."""
    with open(STATE_FILE_PATH, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    assert 'project_id' in data
    assert data['project_id'] == 'PROJ-006-agriculture-optimization'
    assert 'artifact_hashes' in data
    assert isinstance(data['artifact_hashes'], dict)