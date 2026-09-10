"""
Tests for the simulation seed logging utility.
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the function under test
# Note: We mock the default path to use a temporary directory for testing
import sys
from unittest.mock import patch

from code.utils.simulation_seeds import log_simulation_seed

class TestSimulationSeeds:
    def test_logs_seed_correct_format(self, tmp_path):
        """Test that the seed is logged in the exact required format."""
        run_id = "test_run_123"
        seed = 99
        
        # Use the temp directory as the output location
        result_path = log_simulation_seed(run_id, seed, output_dir=str(tmp_path))
        
        # Verify the file exists
        assert os.path.exists(result_path)
        
        # Verify the content
        with open(result_path, "r") as f:
            content = f.read().strip()
        
        expected = f"RUN_ID={run_id} SEED={seed}"
        assert content == expected

    def test_appends_multiple_entries(self, tmp_path):
        """Test that multiple calls append to the file."""
        run_id_1 = "run_A"
        seed_1 = 42
        run_id_2 = "run_B"
        seed_2 = 123
        
        log_simulation_seed(run_id_1, seed_1, output_dir=str(tmp_path))
        log_simulation_seed(run_id_2, seed_2, output_dir=str(tmp_path))
        
        file_path = Path(tmp_path) / "simulation_seeds.txt"
        with open(file_path, "r") as f:
            lines = f.readlines()
        
        assert len(lines) == 2
        assert lines[0].strip() == f"RUN_ID={run_id_1} SEED={seed_1}"
        assert lines[1].strip() == f"RUN_ID={run_id_2} SEED={seed_2}"

    def test_creates_directory_if_missing(self, tmp_path):
        """Test that the function creates the results directory if it doesn't exist."""
        nested_dir = tmp_path / "results" / "subdir"
        run_id = "test"
        seed = 42
        
        # Directory does not exist yet
        assert not nested_dir.exists()
        
        log_simulation_seed(run_id, seed, output_dir=str(nested_dir))
        
        assert nested_dir.exists()
        assert (nested_dir / "simulation_seeds.txt").exists()

    def test_default_seed_is_42(self, tmp_path):
        """Test that the default seed value is 42."""
        run_id = "default_seed_test"
        
        log_simulation_seed(run_id, output_dir=str(tmp_path))
        
        file_path = Path(tmp_path) / "simulation_seeds.txt"
        with open(file_path, "r") as f:
            content = f.read().strip()
        
        assert "SEED=42" in content
