"""
Unit tests for the scheduler trace initialization logic.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

from utils.initialize_trace import initialize_trace_file
from utils.scheduler_trace_schema import SCHEMA_DEFINITION

def test_initialize_trace_creates_schema():
    """Test that initialize_trace_file creates a valid schema structure."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "trace.json"
        initialize_trace_file(output_path)
        
        assert output_path.exists(), "Trace file was not created"
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        # Check schema version
        assert data["schema_version"] == SCHEMA_DEFINITION["properties"]["schema_version"]["const"]
        
        # Check timestamp exists and is valid ISO format
        assert "created_at" in data
        assert "T" in data["created_at"] # Basic ISO check
        
        # Check entries array exists and is empty
        assert "entries" in data
        assert isinstance(data["entries"], list)
        assert len(data["entries"]) == 0

def test_initialize_trace_directory_creation():
    """Test that initialize_trace_file creates parent directories if missing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a nested path that doesn't exist yet
        deep_path = Path(tmp_dir) / "level1" / "level2" / "trace.json"
        
        # This should not raise an error
        initialize_trace_file(deep_path)
        
        assert deep_path.exists(), "Nested directories were not created"

def test_schema_structure_valid():
    """Verify the schema definition matches expected keys."""
    required_keys = ["schema_version", "created_at", "entries"]
    for key in required_keys:
        assert key in SCHEMA_DEFINITION["required"]