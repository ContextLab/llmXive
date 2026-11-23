"""
Tests for T017: Logging and timing of DFTB+ invocations.
Verifies that logs are written in the correct JSON format.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

from utils.dftb_logging import log_dftb_invocation, get_peak_memory_mb, timed_dftb_run

class TestT017Logging:
    
    def test_log_dftb_invocation_creates_file(self, tmp_path):
        """Test that log_dftb_invocation creates the log file."""
        log_file = tmp_path / "test_log.log"
        
        log_dftb_invocation(
            molecule_id="mol_001",
            command="dftb+ test",
            exit_code=0,
            duration=1.5,
            peak_memory_mb=500.0,
            log_file=log_file
        )
        
        assert log_file.exists()
        with open(log_file, 'r') as f:
            content = f.read()
        assert "mol_001" in content
        assert "dftb+ test" in content

    def test_log_dftb_invocation_json_format(self, tmp_path):
        """Test that the log entry is valid JSON with correct schema."""
        log_file = tmp_path / "schema_test.log"
        
        log_dftb_invocation(
            molecule_id="mol_002",
            command="dftb+ geometry_opt",
            exit_code=0,
            duration=2.3,
            peak_memory_mb=1024.5,
            log_file=log_file
        )
        
        with open(log_file, 'r') as f:
            line = f.readline()
        
        entry = json.loads(line)
        
        # Verify schema
        assert entry["molecule_id"] == "mol_002"
        assert entry["command"] == "dftb+ geometry_opt"
        assert entry["exit_code"] == 0
        assert isinstance(entry["duration"], float)
        assert entry["duration"] == 2.3
        assert isinstance(entry["peak_memory_mb"], float)
        assert entry["peak_memory_mb"] == 1024.5
        assert "timestamp" in entry

    def test_log_dftb_invocation_appends(self, tmp_path):
        """Test that multiple calls append to the same file."""
        log_file = tmp_path / "append_test.log"
        
        log_dftb_invocation("mol_1", "cmd1", 0, 1.0, 100.0, log_file)
        log_dftb_invocation("mol_2", "cmd2", 1, 2.0, 200.0, log_file)
        log_dftb_invocation("mol_3", "cmd3", 0, 3.0, 300.0, log_file)
        
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 3
        
        entry1 = json.loads(lines[0])
        entry2 = json.loads(lines[1])
        entry3 = json.loads(lines[2])
        
        assert entry1["molecule_id"] == "mol_1"
        assert entry2["molecule_id"] == "mol_2"
        assert entry3["molecule_id"] == "mol_3"

    def test_get_peak_memory_mb_returns_positive(self):
        """Test that get_peak_memory_mb returns a non-negative value."""
        mem = get_peak_memory_mb()
        assert isinstance(mem, float)
        assert mem >= 0.0

    def test_timed_dftb_run_integration(self, tmp_path):
        """Test the timed_dftb_run context manager."""
        log_file = tmp_path / "timed_test.log"
        
        # Run a simple command that should succeed
        exit_code, duration, memory = timed_dftb_run(
            "test_mol",
            "echo 'hello'",
            log_file=log_file
        )
        
        assert exit_code == 0
        assert duration >= 0.0
        assert memory >= 0.0
        
        # Verify log was written
        assert log_file.exists()
        with open(log_file, 'r') as f:
            entry = json.loads(f.readline())
        
        assert entry["molecule_id"] == "test_mol"
        assert "echo 'hello'" in entry["command"]