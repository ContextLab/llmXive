import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
# We need to handle the relative import structure if running as a module
# But for unit tests, we usually import directly if the path is set up
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.log_memory import (
    get_memory_usage_mb,
    get_peak_memory_mb,
    generate_memory_log_entry,
    save_memory_log,
    log_memory_usage,
    main
)

class TestMemoryFunctions:
    def test_get_memory_usage_mb_returns_positive_float(self):
        """Test that memory usage is a positive number."""
        mem = get_memory_usage_mb()
        assert isinstance(mem, float)
        assert mem > 0

    def test_get_peak_memory_mb_returns_positive_float(self):
        """Test that peak memory usage is a positive number."""
        peak = get_peak_memory_mb()
        assert isinstance(peak, float)
        assert peak > 0

    def test_generate_memory_log_entry_structure(self):
        """Test the structure of a generated log entry."""
        entry = generate_memory_log_entry("test_step", clip_id="clip_001", chunk_index=0)
        
        assert "timestamp" in entry
        assert "step" in entry
        assert "current_memory_mb" in entry
        assert "peak_memory_mb" in entry
        assert "status" in entry
        assert entry["step"] == "test_step"
        assert entry["clip_id"] == "clip_001"
        assert entry["chunk_index"] == 0

    def test_generate_memory_log_entry_optional_fields(self):
        """Test that optional fields are omitted if not provided."""
        entry = generate_memory_log_entry("test_step")
        
        assert "clip_id" not in entry
        assert "chunk_index" not in entry
        assert "message" not in entry

    def test_save_memory_log_creates_file(self):
        """Test that save_memory_log creates a valid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_log.json")
            entries = [
                {"step": "start", "current_memory_mb": 100.0, "peak_memory_mb": 100.0},
                {"step": "end", "current_memory_mb": 105.0, "peak_memory_mb": 105.0}
            ]
            
            save_memory_log(entries, output_path)
            
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            assert loaded == entries

    def test_log_memory_usage_appends_to_list(self):
        """Test that log_memory_usage appends an entry to the provided list."""
        log_entries = []
        entry = log_memory_usage(log_entries, "test", clip_id="c1", chunk_index=1)
        
        assert len(log_entries) == 1
        assert log_entries[0] == entry
        assert entry["clip_id"] == "c1"

class TestMainExecution:
    def test_main_generates_artifacts(self, tmp_path):
        """Test that main() generates the required log files."""
        # Change to a temporary directory to avoid cluttering the project
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Ensure data/processed exists in tmp_path
            Path("data/processed").mkdir(parents=True, exist_ok=True)
            
            # Run main
            main()
            
            # Check artifacts
            log_file = Path("data/processed/extract.log")
            json_file = Path("data/processed/memory_log.json")
            
            assert log_file.exists(), "extract.log was not created"
            assert json_file.exists(), "memory_log.json was not created"
            
            # Verify JSON content is not empty
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            assert len(data) > 0, "memory_log.json is empty"
            assert "step" in data[0], "Log entry missing 'step' field"
            assert "current_memory_mb" in data[0], "Log entry missing memory field"
            
            # Verify log file contains memory info
            with open(log_file, 'r') as f:
                log_content = f.read()
            
            assert "Memory Usage" in log_content, "Log file missing memory usage entries"
            assert "Peak RAM" in log_content, "Log file missing peak RAM entries"
            
        finally:
            os.chdir(original_cwd)