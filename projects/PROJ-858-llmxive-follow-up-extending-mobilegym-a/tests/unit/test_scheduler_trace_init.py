import json
import os
import tempfile
import shutil
from datetime import datetime

import pytest

from utils.scheduler_trace_utils import initialize_trace_file, get_schema_definition, SCHEMA_VERSION

class TestSchedulerTraceInitialization:
    
    def setup_method(self):
        """Create a temporary directory for test artifacts."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = os.path.join(self.temp_dir, "scheduler_trace.json")

    def teardown_method(self):
        """Clean up temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_creates_file_and_directory(self):
        """Test that the function creates the file and necessary directory structure."""
        nested_path = os.path.join(self.temp_dir, "deep", "nested", "path", "scheduler_trace.json")
        
        success = initialize_trace_file(nested_path)
        
        assert success is True
        assert os.path.exists(nested_path)
        
        # Verify directory was created
        assert os.path.exists(os.path.dirname(nested_path))

    def test_file_contains_valid_json(self):
        """Test that the created file is valid JSON."""
        success = initialize_trace_file(self.test_file_path)
        assert success is True
        
        with open(self.test_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert isinstance(data, dict)

    def test_metadata_structure(self):
        """Test that the metadata section matches the expected schema."""
        initialize_trace_file(self.test_file_path)
        
        with open(self.test_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "metadata" in data
        meta = data["metadata"]
        
        assert meta["schema_version"] == SCHEMA_VERSION
        assert "created_at" in meta
        assert "project_id" in meta
        assert meta["project_id"] == "PROJ-858-llmxive-follow-up-extending-mobilegym-a"
        assert "task_id" in meta
        assert meta["task_id"] == "T011"

    def test_entries_is_empty_list(self):
        """Test that the initial entries list is empty."""
        initialize_trace_file(self.test_file_path)
        
        with open(self.test_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "entries" in data
        assert isinstance(data["entries"], list)
        assert len(data["entries"]) == 0

    def test_schema_definition_exists(self):
        """Test that the schema definition function returns a valid schema object."""
        schema = get_schema_definition()
        
        assert isinstance(schema, dict)
        assert "$schema" in schema
        assert schema["type"] == "object"
        assert "metadata" in schema["properties"]
        assert "entries" in schema["properties"]

    def test_timestamp_format(self):
        """Test that the created_at timestamp is in ISO format."""
        initialize_trace_file(self.test_file_path)
        
        with open(self.test_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        created_at = data["metadata"]["created_at"]
        
        # Attempt to parse ISO format
        try:
            datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"Timestamp '{created_at}' is not in valid ISO format")