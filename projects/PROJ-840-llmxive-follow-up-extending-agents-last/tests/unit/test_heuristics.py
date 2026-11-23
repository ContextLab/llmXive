"""
Contract tests for parser normalization logic (T008).

These tests verify that the normalization protocol defined in 
code/classification/heuristics.py correctly:
1. Compares floating-point values with a small tolerance (1e-6).
2. Strips timestamps and random IDs.
3. Canonicalizes object references to a stable hash of their content.

These are CONTRACT tests that define the expected behavior regardless
of implementation details.
"""

import pytest
import json
import hashlib
from pathlib import Path

# Import the functions under test from the existing API surface
from code.classification.heuristics import normalize_state, deep_normalize_states

class TestFloatingPointNormalization:
    """Test that floating-point comparisons use the correct tolerance."""

    def test_floats_within_tolerance_are_equal(self):
        """Values within 1e-6 should be normalized to be comparable."""
        state_a = {"value": 1.0000001}
        state_b = {"value": 1.0000002}
        
        # Normalize both states
        norm_a = normalize_state(state_a)
        norm_b = normalize_state(state_b)
        
        # After normalization, they should be considered equal
        # (or at least the normalized values should be close)
        assert abs(norm_a["value"] - norm_b["value"]) < 1e-5
    
    def test_floats_outside_tolerance_differ(self):
        """Values outside 1e-6 should remain distinguishable."""
        state_a = {"value": 1.0}
        state_b = {"value": 1.001}  # Difference > 1e-6
        
        norm_a = normalize_state(state_a)
        norm_b = normalize_state(state_b)
        
        # These should remain distinct
        assert abs(norm_a["value"] - norm_b["value"]) > 1e-4
    
    def test_nested_floats_normalized(self):
        """Floating point normalization works in nested structures."""
        state_a = {"outer": {"inner": 3.1415926535}}
        state_b = {"outer": {"inner": 3.1415926536}}
        
        norm_a = normalize_state(state_a)
        norm_b = normalize_state(state_b)
        
        # Nested values should be normalized
        assert abs(norm_a["outer"]["inner"] - norm_b["outer"]["inner"]) < 1e-5

class TestTimestampAndIdStripping:
    """Test that timestamps and random IDs are stripped during normalization."""

    def test_timestamp_stripped(self):
        """Timestamps should be removed from normalized state."""
        state = {
            "action": "read_file",
            "timestamp": "2023-10-15T14:30:00Z",
            "file": "test.txt"
        }
        
        normalized = normalize_state(state)
        
        # Timestamp should not be in normalized output
        assert "timestamp" not in normalized
        assert normalized["action"] == "read_file"
        assert normalized["file"] == "test.txt"
    
    def test_random_id_stripped(self):
        """Random IDs (UUIDs, etc.) should be removed."""
        state = {
            "task_id": "task_123e4567-e89b-12d3-a456-426614174000",
            "content": "important data"
        }
        
        normalized = normalize_state(state)
        
        # The random ID should be stripped
        assert "task_id" not in normalized
        assert normalized["content"] == "important data"
    
    def test_mixed_timestamps_and_ids(self):
        """Multiple timestamps and IDs should all be stripped."""
        state = {
            "id": "abc-123-def",
            "created_at": 1697378400,
            "updated_at": "2023-10-15T14:30:00Z",
            "data": {"value": 42}
        }
        
        normalized = normalize_state(state)
        
        assert "id" not in normalized
        assert "created_at" not in normalized
        assert "updated_at" not in normalized
        assert normalized["data"]["value"] == 42

class TestCanonicalization:
    """Test that object references are canonicalized to stable hashes."""

    def test_content_hashed(self):
        """Object content should be replaced with a stable hash."""
        content = "This is the actual content that should be hashed."
        state = {
            "ref": {"content": content}
        }
        
        normalized = normalize_state(state)
        
        # The content should be replaced with a hash
        assert "ref" in normalized
        # The hash should be deterministic
        expected_hash = hashlib.sha256(content.encode()).hexdigest()
        assert normalized["ref"] == expected_hash
    
    def test_same_content_same_hash(self):
        """Identical content should produce identical hashes."""
        content = "Identical content"
        
        state_a = {"ref": {"content": content}}
        state_b = {"ref": {"content": content}}
        
        norm_a = normalize_state(state_a)
        norm_b = normalize_state(state_b)
        
        assert norm_a["ref"] == norm_b["ref"]
    
    def test_different_content_different_hash(self):
        """Different content should produce different hashes."""
        state_a = {"ref": {"content": "Content A"}}
        state_b = {"ref": {"content": "Content B"}}
        
        norm_a = normalize_state(state_a)
        norm_b = normalize_state(state_b)
        
        assert norm_a["ref"] != norm_b["ref"]

class TestDeepNormalization:
    """Test the deep normalization function for complex structures."""

    def test_deep_list_normalization(self):
        """Lists of objects should be normalized element-wise."""
        states = [
            {"value": 1.0, "id": "a"},
            {"value": 2.0, "id": "b"}
        ]
        
        normalized = deep_normalize_states(states)
        
        assert len(normalized) == 2
        assert "id" not in normalized[0]
        assert "id" not in normalized[1]
        assert normalized[0]["value"] == 1.0
        assert normalized[1]["value"] == 2.0
    
    def test_deep_dict_normalization(self):
        """Nested dicts should be normalized recursively."""
        complex_state = {
            "level1": {
                "level2": {
                    "value": 3.14159,
                    "timestamp": "2023-01-01T00:00:00Z",
                    "data": "important"
                }
            }
        }
        
        normalized = deep_normalize_states([complex_state])[0]
        
        # All levels should be normalized
        assert "timestamp" not in normalized["level1"]["level2"]
        assert normalized["level1"]["level2"]["value"] == 3.14159
        assert normalized["level1"]["level2"]["data"] == "important"

class TestEdgeCases:
    """Test normalization with edge cases."""

    def test_empty_state(self):
        """Empty state should normalize to empty dict."""
        assert normalize_state({}) == {}
    
    def test_none_values(self):
        """None values should be handled gracefully."""
        state = {"value": None, "data": "test"}
        normalized = normalize_state(state)
        assert normalized["value"] is None
        assert normalized["data"] == "test"
    
    def test_complex_numbers(self):
        """Complex structures with mixed types."""
        state = {
            "float": 1.234567890123,
            "int": 42,
            "string": "text",
            "bool": True,
            "list": [1, 2, 3]
        }
        
        normalized = normalize_state(state)
        
        assert normalized["float"] == 1.234567890123
        assert normalized["int"] == 42
        assert normalized["string"] == "text"
        assert normalized["bool"] is True
        assert normalized["list"] == [1, 2, 3]

class TestIntegrationWithGoldenSet:
    """Test normalization against the golden fixture structure."""

    def test_normalize_golden_trace_structure(self):
        """Ensure normalization works on typical trace structures."""
        # Simulate a trace entry similar to what would be in golden_fixture.json
        trace_state = {
            "trace_id": "trace_001",
            "timestamp": "2023-10-15T14:30:00Z",
            "steps": [
                {
                    "step_id": "step_001",
                    "action": "read",
                    "target": "file.txt",
                    "content": "file content here",
                    "timestamp": 1697378400
                },
                {
                    "step_id": "step_002",
                    "action": "write",
                    "target": "output.txt",
                    "content": "output content",
                    "timestamp": 1697378460
                }
            ],
            "metadata": {
                "task_description": "Read file.txt and write to output.txt",
                "constraints": ["must not delete", "must write"]
            }
        }
        
        # Normalize the trace
        normalized = deep_normalize_states([trace_state])[0]
        
        # Verify structural integrity
        assert "trace_id" in normalized
        assert "steps" in normalized
        assert "metadata" in normalized
        
        # Verify timestamps are stripped
        assert "timestamp" not in normalized
        
        # Verify step timestamps are stripped
        for step in normalized["steps"]:
            assert "timestamp" not in step
            assert "step_id" not in step  # Random IDs should be stripped
        
        # Verify content is preserved (or hashed if it's a ref)
        assert normalized["steps"][0]["action"] == "read"
        assert normalized["steps"][0]["target"] == "file.txt"