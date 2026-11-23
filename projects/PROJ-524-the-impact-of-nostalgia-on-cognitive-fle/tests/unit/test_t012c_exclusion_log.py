"""
Unit tests for T012c: Generate Exclusion Log.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
import sys
sys.path.insert(0, str(project_root / "code"))

from task_t012c_generate_exclusion_log import (
    load_exclusion_counts,
    check_simulation_fallback,
    generate_exclusion_log,
    EXCLUSION_COUNTS_PATH,
    METADATA_PATH,
    OUTPUT_PATH
)


class TestLoadExclusionCounts:
    def test_load_existing_counts(self, tmp_path):
        # Create a temporary exclusion_counts.json
        counts_data = {
            "ERR_MISSING_AGE_FIELD": 5,
            "ERR_MISSING_SCORE": 2,
            "ERR_MMSE_IMPAIRED": 0
        }
        
        # Mock the global path to point to temp dir
        temp_counts = tmp_path / "exclusion_counts.json"
        with open(temp_counts, "w") as f:
            json.dump(counts_data, f)
        
        with patch("task_t012c_generate_exclusion_log.EXCLUSION_COUNTS_PATH", temp_counts):
            result = load_exclusion_counts()
            assert result == counts_data

    def test_missing_file_raises(self, tmp_path):
        # Point to a non-existent file
        missing_path = tmp_path / "non_existent.json"
        with patch("task_t012c_generate_exclusion_log.EXCLUSION_COUNTS_PATH", missing_path):
            with pytest.raises(FileNotFoundError):
                load_exclusion_counts()


class TestCheckSimulationFallback:
    def test_sim_true(self, tmp_path):
        metadata = {"simulation_mode": True}
        temp_meta = tmp_path / "metadata.json"
        with open(temp_meta, "w") as f:
            json.dump(metadata, f)
        
        with patch("task_t012c_generate_exclusion_log.METADATA_PATH", temp_meta):
            assert check_simulation_fallback() is True

    def test_sim_false(self, tmp_path):
        metadata = {"simulation_mode": False}
        temp_meta = tmp_path / "metadata.json"
        with open(temp_meta, "w") as f:
            json.dump(metadata, f)
        
        with patch("task_t012c_generate_exclusion_log.METADATA_PATH", temp_meta):
            assert check_simulation_fallback() is False

    def test_missing_file_returns_false(self, tmp_path):
        missing_path = tmp_path / "non_existent.json"
        with patch("task_t012c_generate_exclusion_log.METADATA_PATH", missing_path):
            assert check_simulation_fallback() is False


class TestGenerateExclusionLog:
    def test_full_generation(self, tmp_path):
        # Setup temp files
        counts_data = {
            "ERR_MISSING_AGE_FIELD": 10,
            "ERR_MISSING_SCORE": 5,
            "ERR_MMSE_IMPAIRED": 2
        }
        counts_file = tmp_path / "exclusion_counts.json"
        with open(counts_file, "w") as f:
            json.dump(counts_data, f)

        meta_data = {"simulation_mode": True}
        meta_file = tmp_path / "metadata.json"
        with open(meta_file, "w") as f:
            json.dump(meta_data, f)

        with patch("task_t012c_generate_exclusion_log.EXCLUSION_COUNTS_PATH", counts_file), \
             patch("task_t012c_generate_exclusion_log.METADATA_PATH", meta_file):
            
            log = generate_exclusion_log()
            
            assert log["ERR_MISSING_AGE_FIELD"] == 10
            assert log["ERR_MISSING_SCORE"] == 5
            assert log["ERR_MMSE_IMPAIRED"] == 2
            assert log["SIMULATION_FALLBACK"] is True
            assert "timestamp" in log