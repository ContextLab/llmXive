"""
Unit tests for Task T012c: Generate Exclusion Log
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add parent directory to path to import task module
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from task_t012c_generate_exclusion_log import (
    load_exclusion_counts,
    check_simulation_fallback,
    generate_exclusion_log,
    EXCLUSION_COUNTS_PATH,
    EXCLUSION_LOG_PATH,
    METADATA_PATH
)

@pytest.fixture
def temp_dirs():
    """Create temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        processed_dir = tmpdir_path / "data" / "processed"
        raw_dir = tmpdir_path / "data" / "raw"
        processed_dir.mkdir(parents=True)
        raw_dir.mkdir(parents=True)

        # Patch paths
        with patch('task_t012c_generate_exclusion_log.PROCESSED_DIR', processed_dir):
            with patch('task_t012c_generate_exclusion_log.EXCLUSION_COUNTS_PATH', processed_dir / "exclusion_counts.json"):
                with patch('task_t012c_generate_exclusion_log.EXCLUSION_LOG_PATH', processed_dir / "exclusion_log.json"):
                    with patch('task_t012c_generate_exclusion_log.METADATA_PATH', raw_dir / "metadata.json"):
                        yield {
                            "processed": processed_dir,
                            "raw": raw_dir
                        }

def test_load_exclusion_counts_success(temp_dirs):
    """Test loading exclusion counts when file exists."""
    counts_data = {
        "ERR_MISSING_AGE_FIELD": 5,
        "ERR_MISSING_SCORE": 2,
        "ERR_MMSE_IMPAIRED": 1
    }
    with open(temp_dirs["processed"] / "exclusion_counts.json", 'w') as f:
        json.dump(counts_data, f)

    result = load_exclusion_counts()
    assert result == counts_data
    assert result["ERR_MISSING_AGE_FIELD"] == 5

def test_load_exclusion_counts_missing_file(temp_dirs):
    """Test that FileNotFoundError is raised when counts file is missing."""
    with pytest.raises(FileNotFoundError):
        load_exclusion_counts()

def test_check_simulation_fallback_true(temp_dirs):
    """Test simulation fallback check when mode is True."""
    metadata = {"simulation_mode": True}
    with open(temp_dirs["raw"] / "metadata.json", 'w') as f:
        json.dump(metadata, f)

    result = check_simulation_fallback()
    assert result is True

def test_check_simulation_fallback_false(temp_dirs):
    """Test simulation fallback check when mode is False."""
    metadata = {"simulation_mode": False}
    with open(temp_dirs["raw"] / "metadata.json", 'w') as f:
        json.dump(metadata, f)

    result = check_simulation_fallback()
    assert result is False

def test_check_simulation_fallback_missing_metadata(temp_dirs):
    """Test simulation fallback check when metadata file is missing."""
    result = check_simulation_fallback()
    assert result is False

def test_generate_exclusion_log(temp_dirs):
    """Test full generation of exclusion log."""
    # Setup counts
    counts_data = {
        "ERR_MISSING_AGE_FIELD": 10,
        "ERR_MISSING_SCORE": 0,
        "ERR_MMSE_IMPAIRED": 3
    }
    with open(temp_dirs["processed"] / "exclusion_counts.json", 'w') as f:
        json.dump(counts_data, f)

    # Setup metadata
    metadata = {"simulation_mode": True}
    with open(temp_dirs["raw"] / "metadata.json", 'w') as f:
        json.dump(metadata, f)

    log_entry = generate_exclusion_log()

    assert "timestamp" in log_entry
    assert log_entry["task_id"] == "T012c"
    assert log_entry["exclusion_counts"]["ERR_MISSING_AGE_FIELD"] == 10
    assert log_entry["exclusion_counts"]["ERR_MISSING_SCORE"] == 0
    assert log_entry["exclusion_counts"]["ERR_MMSE_IMPAIRED"] == 3
    assert log_entry["SIMULATION_FALLBACK"] is True