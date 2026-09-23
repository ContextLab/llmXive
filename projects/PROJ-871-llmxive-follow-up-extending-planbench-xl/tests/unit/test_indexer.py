"""
Unit tests for the signature index construction (T016).

This module verifies the static JSON index creation with consistent schema
as defined in the project specifications for US2.

Tests:
- test_load_injected_data: Verifies loading of the injected failure subset.
- test_extract_failure_signatures: Verifies extraction of patterns and tool IDs.
- test_build_failure_index: Verifies the construction of the index dictionary.
- test_save_index: Verifies the file I/O and JSON serialization.
- test_schema_consistency: Verifies the output JSON matches the required schema
  (tool_id, pattern_string, recovery_strategy) and that recovery_strategy is uniform.
- test_empty_input_handling: Verifies behavior when no injected data is found.
"""

import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions from the indexer module
# Using relative imports logic adapted for the test environment structure
# The actual import path depends on how pytest is run, but we assume
# the project root is in sys.path or we import via the package structure.
# Based on the API surface, we import from dataset.indexer.
try:
    from code.dataset.indexer import (
        load_injected_data,
        extract_failure_signatures,
        build_failure_index,
        save_index
    )
except ImportError:
    # Fallback for direct execution in project root context
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from code.dataset.indexer import (
        load_injected_data,
        extract_failure_signatures,
        build_failure_index,
        save_index
    )

from code.utils.config import get_path


class TestIndexerConstruction:
    """Test suite for the failure signature index construction logic."""

    @pytest.fixture
    def sample_injected_data(self):
        """Create a temporary JSONL file with sample injected failure data."""
        data = [
            {
                "task_id": "task_001",
                "ground_truth": "success",
                "tool_outputs": [
                    {"tool_id": "tool_A", "output": "ERROR: silent_tool_failure"},
                    {"tool_id": "tool_B", "output": "Success"}
                ],
                "injected_error_pattern": "silent_tool_failure"
            },
            {
                "task_id": "task_002",
                "ground_truth": "success",
                "tool_outputs": [
                    {"tool_id": "tool_C", "output": "ERROR: connection_timeout"}
                ],
                "injected_error_pattern": "connection_timeout"
            }
        ]
        
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, "implicit_failure_subset.jsonl")
        
        with open(file_path, "w") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")
        
        return file_path, temp_dir

    @pytest.fixture
    def mock_config_path(self, sample_injected_data):
        """Mock the get_path function to return our temporary file."""
        injected_file, temp_dir = sample_injected_data
        
        with patch('code.dataset.indexer.get_path') as mock_get_path:
            mock_get_path.return_value = injected_file
            yield injected_file, temp_dir
            # Cleanup
            import shutil
            shutil.rmtree(temp_dir)

    def test_load_injected_data(self, mock_config_path):
        """Test that load_injected_data correctly reads the JSONL file."""
        file_path, _ = mock_config_path
        
        # Reload the function to ensure it uses the mocked path if necessary,
        # or just call it assuming the module uses the mocked config.
        # Since we patched get_path, the module's internal call should use it.
        data = load_injected_data()
        
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["task_id"] == "task_001"
        assert "injected_error_pattern" in data[0]

    def test_extract_failure_signatures(self, mock_config_path):
        """Test extraction of signatures from injected data."""
        file_path, _ = mock_config_path
        
        data = load_injected_data()
        signatures = extract_failure_signatures(data)
        
        assert isinstance(signatures, list)
        assert len(signatures) == 2
        
        # Check structure
        for sig in signatures:
            assert "tool_id" in sig
            assert "pattern_string" in sig
            assert "recovery_strategy" in sig
            assert sig["recovery_strategy"] == "replan" # As per spec

        # Check specific values
        tool_ids = [s["tool_id"] for s in signatures]
        assert "tool_A" in tool_ids
        assert "tool_C" in tool_ids

    def test_build_failure_index(self, mock_config_path):
        """Test building the final index dictionary."""
        file_path, _ = mock_config_path
        
        data = load_injected_data()
        signatures = extract_failure_signatures(data)
        index = build_failure_index(signatures)
        
        assert isinstance(index, dict)
        assert "tool_A" in index
        assert index["tool_A"]["pattern_string"] == "ERROR: silent_tool_failure"
        assert index["tool_A"]["recovery_strategy"] == "replan"

    def test_save_index(self, mock_config_path):
        """Test saving the index to a JSON file."""
        file_path, temp_dir = mock_config_path
        
        data = load_injected_data()
        signatures = extract_failure_signatures(data)
        index = build_failure_index(signatures)
        
        output_file = os.path.join(temp_dir, "failure_signatures.json")
        
        # Mock get_path for the output if needed, but we can just pass the path
        # to save_index if the function signature allows, or patch it.
        # Looking at the API surface, save_index likely uses get_path for output.
        # We will patch the output path retrieval.
        
        with patch('code.dataset.indexer.get_path') as mock_get_path:
            # First call returns input, second returns output
            def side_effect(key):
                if key == "derived/implicit_failure_subset":
                    return file_path
                elif key == "derived/failure_signatures":
                    return output_file
                return None
            
            mock_get_path.side_effect = side_effect
            
            save_index() # Assuming it calls get_path internally for both
            
            assert os.path.exists(output_file)
            
            with open(output_file, "r") as f:
                saved_index = json.load(f)
            
            assert "tool_A" in saved_index
            assert saved_index["tool_A"]["recovery_strategy"] == "replan"

    def test_schema_consistency(self, mock_config_path):
        """Verify the output JSON strictly matches the required schema."""
        file_path, temp_dir = mock_config_path
        
        data = load_injected_data()
        signatures = extract_failure_signatures(data)
        index = build_failure_index(signatures)
        
        # Validate schema
        required_keys = {"tool_id", "pattern_string", "recovery_strategy"}
        
        for tool_id, entry in index.items():
            assert isinstance(tool_id, str)
            assert isinstance(entry, dict)
            assert set(entry.keys()) == required_keys
            assert isinstance(entry["pattern_string"], str)
            assert isinstance(entry["recovery_strategy"], str)
            # Enforce consistent recovery strategy
            assert entry["recovery_strategy"] == "replan", \
                f"recovery_strategy must be 'replan', got {entry['recovery_strategy']}"

    def test_empty_input_handling(self):
        """Test behavior when the injected data list is empty."""
        empty_data = []
        
        signatures = extract_failure_signatures(empty_data)
        assert signatures == []
        
        index = build_failure_index(signatures)
        assert index == {}

    def test_wildcard_pattern_handling(self):
        """Test that patterns with wildcards are handled correctly in extraction."""
        # Simulate data with a wildcard pattern (though injector usually creates specific ones)
        # The indexer logic should preserve the string as is.
        data = [
            {
                "task_id": "task_003",
                "tool_outputs": [
                    {"tool_id": "tool_D", "output": "ERROR: *failure*"}
                ],
                "injected_error_pattern": "*failure*"
            }
        ]
        
        signatures = extract_failure_signatures(data)
        assert len(signatures) == 1
        assert signatures[0]["pattern_string"] == "*failure*"
        # The actual matching logic is in the agent, but the indexer must store it correctly.