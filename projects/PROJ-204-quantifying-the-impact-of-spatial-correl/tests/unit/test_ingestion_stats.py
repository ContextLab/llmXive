"""
Unit tests for ingestion stats calculation (T010b).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

import sys
# Add code to path if not already
if "code" not in sys.path:
    sys.path.insert(0, "code")

from utils.ingestion_stats import calculate_ingestion_stats, write_ingestion_stats, load_yaml_safe

class TestIngestionStats:
    @pytest.fixture
    def temp_state_dir(self):
        """Create a temporary directory for state files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_load_yaml_safe_existing(self, temp_state_dir):
        """Test loading an existing valid YAML file."""
        test_file = temp_state_dir / "test.yaml"
        data = {"status": "success", "value": 123}
        with open(test_file, 'w') as f:
            yaml.dump(data, f)
        
        result = load_yaml_safe(test_file)
        assert result == data

    def test_load_yaml_safe_missing(self, temp_state_dir):
        """Test loading a missing YAML file returns None."""
        missing_file = temp_state_dir / "missing.yaml"
        result = load_yaml_safe(missing_file)
        assert result is None

    def test_calculate_stats_success_with_log(self, temp_state_dir):
        """Test calculation when download log indicates success."""
        # Create feasibility file
        feas_file = temp_state_dir / "data_feasibility_status.yaml"
        feas_data = {"status": "success", "source_url": "http://example.com/data"}
        with open(feas_file, 'w') as f:
            yaml.dump(feas_data, f)
        
        # Create download log
        log_file = temp_state_dir / "download_status.yaml"
        log_data = {"status": "success", "n_requested": 10, "n_processed": 8}
        with open(log_file, 'w') as f:
            yaml.dump(log_data, f)
        
        stats = calculate_ingestion_stats(temp_state_dir)
        
        assert stats["status"] == "success"
        assert stats["n_requested"] == 10
        assert stats["n_processed"] == 8
        assert abs(stats["ingestion_success_rate"] - 0.8) < 1e-6
        assert stats["source_url"] == "http://example.com/data"

    def test_calculate_stats_failed_feasibility(self, temp_state_dir):
        """Test calculation when feasibility check failed."""
        feas_file = temp_state_dir / "data_feasibility_status.yaml"
        feas_data = {"status": "failed", "reason": "No source found"}
        with open(feas_file, 'w') as f:
            yaml.dump(feas_data, f)
        
        stats = calculate_ingestion_stats(temp_state_dir)
        
        assert stats["status"] == "failed_no_source"
        assert stats["n_requested"] == 0
        assert stats["n_processed"] == 0
        assert stats["ingestion_success_rate"] == 0.0

    def test_write_ingestion_stats(self, temp_state_dir):
        """Test writing stats to JSON."""
        stats = {
            "n_requested": 5,
            "n_processed": 5,
            "ingestion_success_rate": 1.0,
            "status": "success",
            "source_url": "http://test.com"
        }
        output_file = temp_state_dir / "ingestion_stats.json"
        
        write_ingestion_stats(stats, output_file)
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            loaded_stats = json.load(f)
        
        assert loaded_stats == stats