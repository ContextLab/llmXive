"""
Unit tests for T018: update_readme_exclusions.py
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# We will mock the config import to use a temp directory
# Since we can't easily import the real config without setting up the full env,
# we will test the logic functions directly by passing paths.

from code.update_readme_exclusions import generate_exclusion_section, load_exclusion_log

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp)

def test_generate_exclusion_section_empty():
    """Test that an empty list generates the 'no exclusions' message."""
    result = generate_exclusion_section([])
    assert "No datasets were excluded" in result
    assert "### Exclusion Logs" in result

def test_generate_exclusion_section_single():
    """Test generation with a single exclusion entry."""
    exclusions = [
        {"dataset_id": "123", "source": "openml", "reason": "Missing sequential stimuli"}
    ]
    result = generate_exclusion_section(exclusions)
    
    assert "### Exclusion Logs" in result
    assert "| 123 | openml | Missing sequential stimuli | Excluded |" in result
    assert "Generated:" in result

def test_generate_exclusion_section_multiple():
    """Test generation with multiple entries."""
    exclusions = [
        {"dataset_id": "123", "source": "openml", "reason": "Missing sequential stimuli"},
        {"dataset_id": "456", "source": "hf", "reason": "Non-sequential noise"}
    ]
    result = generate_exclusion_section(exclusions)
    
    assert "| 123 | openml | Missing sequential stimuli | Excluded |" in result
    assert "| 456 | hf | Non-sequential noise | Excluded |" in result

def test_load_exclusion_log_file_not_found(temp_dir):
    """Test behavior when exclusion log file is missing."""
    # Temporarily change the global path for the test function
    # Since the function uses a global constant, we need to patch it or pass a mock
    # For this unit test, we'll test the logic by mocking the file existence
    
    with patch('code.update_readme_exclusions.EXCLUSION_LOG_PATH', temp_dir / "nonexistent.json"):
        with patch('code.update_readme_exclusions.logger') as mock_logger:
            result = load_exclusion_log()
            assert result == []
            mock_logger.warning.assert_called_once()

def test_load_exclusion_log_valid_json(temp_dir):
    """Test loading a valid JSON exclusion log."""
    log_path = temp_dir / "exclusion_log.json"
    data = [
        {"dataset_id": "999", "source": "test", "reason": "Bad data"}
    ]
    with open(log_path, 'w') as f:
        json.dump(data, f)
    
    with patch('code.update_readme_exclusions.EXCLUSION_LOG_PATH', log_path):
        result = load_exclusion_log()
        assert len(result) == 1
        assert result[0]["dataset_id"] == "999"

def test_load_exclusion_log_dict_format(temp_dir):
    """Test loading a JSON file that wraps the list in a dict."""
    log_path = temp_dir / "exclusion_log.json"
    data = {
        "exclusions": [
            {"dataset_id": "888", "source": "test", "reason": "Invalid"}
        ]
    }
    with open(log_path, 'w') as f:
        json.dump(data, f)
    
    with patch('code.update_readme_exclusions.EXCLUSION_LOG_PATH', log_path):
        result = load_exclusion_log()
        assert len(result) == 1
        assert result[0]["dataset_id"] == "888"