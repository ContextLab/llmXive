"""
Unit tests for the normalization protocol in code/classification/heuristics.py.

These tests verify the contract for normalize_state, specifically:
- Float tolerance normalization (FR-001) using exactly 1e-6.
- Stripping or canonicalizing timestamp and ID fields.
- Handling nested structures, None values, strings, and lists.
"""
import pytest
from classification.heuristics import normalize_state


class TestNormalizeState:
    def test_normalize_float_tolerance(self):
        """
        Verify float normalization with 1e-6 tolerance (FR-001).
        
        Values within 1e-6 of a baseline (or integer) should be normalized
        to a canonical representation (e.g., rounded or zeroed relative to baseline).
        """
        state = {
            "position": 1.0000001,
            "velocity": 2.0000009,
            "angle": 3.0000004,
            "exact_match": 1.0
        }
        
        normalized = normalize_state(state)
        
        assert isinstance(normalized, dict)
        assert "position" in normalized
        assert "velocity" in normalized
        assert "angle" in normalized
        assert "exact_match" in normalized
        
        # Check that values close to integers are normalized to the integer
        # within the 1e-6 tolerance defined in heuristics.py
        assert normalized["position"] == 1.0
        assert normalized["velocity"] == 2.0
        assert normalized["angle"] == 3.0
        assert normalized["exact_match"] == 1.0
    
    def test_normalize_float_tolerance_failure(self):
        """
        Verify that floats NOT within 1e-6 tolerance are preserved as floats.
        """
        state = {
            "distance": 1.0001,  # > 1e-6 from 1.0
            "time": 2.5
        }
        
        normalized = normalize_state(state)
        
        assert normalized["distance"] == 1.0001
        assert normalized["time"] == 2.5
    
    def test_normalize_timestamp_stripping(self):
        """
        Verify timestamp fields are stripped or normalized.
        
        Per FR-001, timestamp fields should be removed or canonicalized.
        We expect 'timestamp' key to be absent or normalized to a placeholder.
        """
        state = {
            "step_id": "step_001",
            "timestamp": 1234567890.123456,
            "data": {"value": 10}
        }
        
        normalized = normalize_state(state)
        
        assert isinstance(normalized, dict)
        # The 'timestamp' key should be removed or normalized
        assert "timestamp" not in normalized
        # Other keys should remain
        assert "step_id" in normalized
        assert "data" in normalized
    
    def test_normalize_id_stripping(self):
        """
        Verify ID fields (unique_id, task_id) are stripped or normalized.
        """
        state = {
            "unique_id": "abc-123-def",
            "task_id": "task_001",
            "value": 42
        }
        
        normalized = normalize_state(state)
        
        assert isinstance(normalized, dict)
        # ID fields should be removed
        assert "unique_id" not in normalized
        assert "task_id" not in normalized
        assert "value" in normalized
    
    def test_normalize_nested_structures(self):
        """
        Verify nested structures are handled recursively.
        """
        state = {
            "outer": {
                "inner": {
                    "value": 1.0000001,
                    "timestamp": 999.999
                }
            }
        }
        
        normalized = normalize_state(state)
        
        assert isinstance(normalized, dict)
        assert "outer" in normalized
        assert isinstance(normalized["outer"], dict)
        assert "inner" in normalized["outer"]
        assert isinstance(normalized["outer"]["inner"], dict)
        
        # Check normalization in nested structure
        assert normalized["outer"]["inner"]["value"] == 1.0
        assert "timestamp" not in normalized["outer"]["inner"]
    
    def test_normalize_empty_state(self):
        """
        Verify empty state handling.
        """
        state = {}
        normalized = normalize_state(state)
        assert normalized == {}
    
    def test_normalize_none_values(self):
        """
        Verify None value handling.
        """
        state = {
            "value": None,
            "number": 42
        }
        
        normalized = normalize_state(state)
        assert isinstance(normalized, dict)
        assert normalized["value"] is None
        assert normalized["number"] == 42
    
    def test_normalize_string_values(self):
        """
        Verify string value handling.
        """
        state = {
            "text": "hello world",
            "code": "print('test')"
        }
        
        normalized = normalize_state(state)
        assert normalized["text"] == "hello world"
        assert normalized["code"] == "print('test')"
    
    def test_normalize_list_values(self):
        """
        Verify list value handling, including nested floats.
        """
        state = {
            "items": [1, 2, 3],
            "floats": [1.0000001, 2.0000009, 3.5]
        }
        
        normalized = normalize_state(state)
        assert isinstance(normalized["items"], list)
        assert len(normalized["items"]) == 3
        assert normalized["items"] == [1, 2, 3]
        
        assert isinstance(normalized["floats"], list)
        assert len(normalized["floats"]) == 3
        # Check float normalization in list
        assert normalized["floats"][0] == 1.0
        assert normalized["floats"][1] == 2.0
        assert normalized["floats"][2] == 3.5
    
    def test_normalize_mixed_types(self):
        """
        Verify handling of mixed types in a single state.
        """
        state = {
            "id": "some-id",
            "ts": 123.456,
            "float_close": 5.0000001,
            "float_far": 5.001,
            "nested": {
                "id": "inner-id",
                "val": 10.0000002
            }
        }
        
        normalized = normalize_state(state)
        
        # IDs stripped
        assert "id" not in normalized
        assert "ts" not in normalized
        assert "id" not in normalized["nested"]
        
        # Floats normalized
        assert normalized["float_close"] == 5.0
        assert normalized["float_far"] == 5.001
        assert normalized["nested"]["val"] == 10.0