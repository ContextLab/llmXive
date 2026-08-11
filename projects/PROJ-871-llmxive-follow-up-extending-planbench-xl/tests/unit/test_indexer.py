"""
Unit tests for the failure signature indexer (T009b).

Verifies that:
1. The indexer correctly loads JSONL data.
2. It extracts error patterns only from tasks marked with `injected_error`.
3. It maps patterns to the correct tool identifiers.
4. It produces a valid JSON structure for the index.
"""
import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module functions
from code.dataset.indexer import (
    load_injected_data,
    extract_failure_signatures,
    build_failure_index,
    save_index,
    main
)
from code.utils.config import get_path

class TestIndexer:
    
    def test_extract_failure_signatures_empty_list(self):
        """Test that an empty task list returns an empty index."""
        result = extract_failure_signatures([])
        assert result == {}
        
    def test_extract_failure_signatures_no_errors(self):
        """Test that tasks without errors are ignored."""
        tasks = [
            {
                "task_id": "1",
                "injected_error": False,
                "tool_outputs": ["Success: result A", "Success: result B"]
            }
        ]
        result = extract_failure_signatures(tasks)
        assert result == {}
        
    def test_extract_failure_signatures_with_errors(self):
        """Test extraction of error patterns and tool mapping."""
        tasks = [
            {
                "task_id": "1",
                "injected_error": True,
                "tool_id": "tool_alpha",
                "tool_outputs": [
                    "Success: data loaded",
                    "ERROR: silent_tool_failure"
                ]
            },
            {
                "task_id": "2",
                "injected_error": True,
                "tool_id": "tool_beta",
                "tool_outputs": [
                    "ERROR: connection_timeout"
                ]
            },
            {
                "task_id": "3",
                "injected_error": False,
                "tool_id": "tool_gamma",
                "tool_outputs": [
                    "ERROR: this_should_be_ignored"
                ]
            }
        ]
        
        result = extract_failure_signatures(tasks)
        
        # Should have 2 entries
        assert len(result) == 2
        
        # Check first pattern
        assert "ERROR: silent_tool_failure" in result
        assert result["ERROR: silent_tool_failure"]["tool_id"] == "tool_alpha"
        assert result["ERROR: silent_tool_failure"]["recovery_strategy"] == "replan"
        
        # Check second pattern
        assert "ERROR: connection_timeout" in result
        assert result["ERROR: connection_timeout"]["tool_id"] == "tool_beta"
        
        # Verify the non-injected error was ignored
        assert "ERROR: this_should_be_ignored" not in result

    def test_extract_failure_signatures_duplicate_patterns(self):
        """Test that duplicate error patterns from different tasks are handled."""
        tasks = [
            {
                "task_id": "1",
                "injected_error": True,
                "tool_id": "tool_x",
                "tool_outputs": ["ERROR: generic_failure"]
            },
            {
                "task_id": "2",
                "injected_error": True,
                "tool_id": "tool_y",
                "tool_outputs": ["ERROR: generic_failure"]
            }
        ]
        
        result = extract_failure_signatures(tasks)
        
        # Should have 1 entry (deduplicated by pattern)
        assert len(result) == 1
        assert "ERROR: generic_failure" in result
        # The tool_id will be from the first occurrence (deterministic order)
        assert result["ERROR: generic_failure"]["tool_id"] == "tool_x"

    def test_save_index_creates_file(self, tmp_path):
        """Test that save_index writes a valid JSON file."""
        index = {
            "ERROR: test": {
                "tool_id": "test_tool",
                "recovery_strategy": "replan"
            }
        }
        output_file = tmp_path / "test_index.json"
        
        result_path = save_index(index, str(output_file))
        
        assert os.path.exists(result_path)
        assert result_path == str(output_file)
        
        with open(result_path, 'r') as f:
            loaded = json.load(f)
            
        assert loaded == index

    def test_load_injected_data_file_not_found(self):
        """Test that load_injected_data raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_injected_data("/nonexistent/path/file.jsonl")

    def test_load_injected_data_valid_jsonl(self, tmp_path):
        """Test loading a valid JSONL file."""
        data_file = tmp_path / "data.jsonl"
        data = [
            {"task_id": "1", "injected_error": True, "tool_outputs": ["Error"]},
            {"task_id": "2", "injected_error": False, "tool_outputs": ["Ok"]}
        ]
        
        with open(data_file, 'w') as f:
            for item in data:
                f.write(json.dumps(item) + "\n")
        
        result = load_injected_data(str(data_file))
        assert len(result) == 2
        assert result[0]["task_id"] == "1"
        assert result[1]["task_id"] == "2"

    @patch('code.dataset.indexer.load_injected_data')
    @patch('code.dataset.indexer.extract_failure_signatures')
    @patch('code.dataset.indexer.build_failure_index')
    @patch('code.dataset.indexer.save_index')
    def test_main_flow(self, mock_save, mock_build, mock_extract, mock_load):
        """Test the main function orchestrates correctly."""
        mock_load.return_value = [{"task_id": "1"}]
        mock_extract.return_value = {"pattern": {"tool_id": "t"}}
        mock_build.return_value = {"pattern": {"tool_id": "t"}}
        mock_save.return_value = "/output/path.json"
        
        with patch('builtins.print'):
            main()
        
        mock_load.assert_called_once()
        mock_extract.assert_called_once_with(mock_load.return_value)
        mock_build.assert_called_once_with(mock_extract.return_value)
        mock_save.assert_called_once_with(mock_build.return_value)