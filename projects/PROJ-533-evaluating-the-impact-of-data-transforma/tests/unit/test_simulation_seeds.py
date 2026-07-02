"""
Unit tests for simulation seed logging functionality.
"""
import pytest
from pathlib import Path
import os
import tempfile
from code.utils.simulation_seeds import log_simulation_seed

class TestSimulationSeeds:
    def test_log_simulation_seed_creates_file(self, tmp_path):
        """Test that log_simulation_seed creates the output file."""
        output_path = str(tmp_path / "seeds.txt")
        run_id = "test_run_001"
        seed = 42
        
        log_simulation_seed(run_id, seed, output_path)
        
        assert os.path.exists(output_path)
        
        with open(output_path, "r") as f:
            content = f.read()
        
        assert f"RUN_ID={run_id}" in content
        assert f"SEED={seed}" in content

    def test_log_simulation_seed_appends(self, tmp_path):
        """Test that multiple calls append to the file."""
        output_path = str(tmp_path / "seeds.txt")
        
        log_simulation_seed("run_1", 10, output_path)
        log_simulation_seed("run_2", 20, output_path)
        
        with open(output_path, "r") as f:
            lines = f.readlines()
        
        assert len(lines) == 2
        assert "RUN_ID=run_1 SEED=10" in lines[0]
        assert "RUN_ID=run_2 SEED=20" in lines[1]

    def test_log_simulation_seed_format(self, tmp_path):
        """Test the exact format of the log entry."""
        output_path = str(tmp_path / "seeds.txt")
        
        log_simulation_seed("specific_run", 12345, output_path)
        
        with open(output_path, "r") as f:
            content = f.read().strip()
        
        assert content == "RUN_ID=specific_run SEED=12345"