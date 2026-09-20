"""
Unit tests for the scheduler trace initialization (T011).

Verifies that the trace file is created with the correct schema structure.
"""
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime, timezone

import pytest

from utils.initialize_trace import initialize_trace_file
from utils.scheduler_trace_schema import get_initial_trace_content, SCHEMA_VERSION, validate_trace_entry

class TestTraceInitialization:
    """Tests for T011: Initialize scheduler trace schema and directory structure."""

    def test_initial_trace_content_structure(self):
        """Verify the initial content has the required schema fields."""
        content = get_initial_trace_content()
        
        assert "schema_version" in content
        assert content["schema_version"] == SCHEMA_VERSION
        assert "created_at" in content
        assert "entries" in content
        assert isinstance(content["entries"], list)
        
        # Verify timestamp format
        datetime.fromisoformat(content["created_at"].replace('Z', '+00:00'))

    def test_trace_file_creation(self, tmp_path):
        """Verify the trace file is created correctly."""
        output_path = tmp_path / "test_trace.json"
        
        result_path = initialize_trace_file(output_path)
        
        assert result_path.exists()
        assert result_path == output_path
        
        with open(result_path, 'r') as f:
            data = json.load(f)
        
        assert data["schema_version"] == SCHEMA_VERSION
        assert isinstance(data["entries"], list)
        assert len(data["entries"]) == 0

    def test_trace_file_not_overwritten(self, tmp_path):
        """Verify existing trace files are not overwritten."""
        output_path = tmp_path / "existing_trace.json"
        
        # Create a file with dummy content
        output_path.write_text('{"schema_version": "0.0.0", "entries": ["test"]}')
        
        result_path = initialize_trace_file(output_path)
        
        assert result_path.exists()
        
        with open(result_path, 'r') as f:
            data = json.load(f)
        
        # Should remain unchanged
        assert data["schema_version"] == "0.0.0"
        assert data["entries"] == ["test"]

    def test_validate_trace_entry_valid(self):
        """Test validation of a valid trace entry."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "metrics_triggered",
            "data": {
                "metrics_triggered": [
                    {"variable_name": "dark_mode", "transition_value": True}
                ]
            }
        }
        assert validate_trace_entry(entry) is True

    def test_validate_trace_entry_invalid_missing_keys(self):
        """Test validation fails on missing required keys."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            # Missing event_type and data
        }
        assert validate_trace_entry(entry) is False

    def test_validate_trace_entry_invalid_event_type(self):
        """Test validation fails on invalid event type."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "invalid_event",
            "data": {}
        }
        assert validate_trace_entry(entry) is False

    def test_validate_trace_entry_invalid_data_type(self):
        """Test validation fails if data is not a dict."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "scheduler_start",
            "data": "string_instead_of_dict"
        }
        assert validate_trace_entry(entry) is False
