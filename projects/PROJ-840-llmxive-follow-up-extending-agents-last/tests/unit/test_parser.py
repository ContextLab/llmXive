import pytest
import json
from classification.parser import parse_ale_trace

class TestParseAleTrace:
    def test_parse_valid_trace(self, tmp_path):
        """Verify parsing of valid ALE trace."""
        trace_data = {
            "trace_id": "test_001",
            "steps": [
                {
                    "step_id": 1,
                    "action": "move",
                    "state": {"x": 1.0, "y": 2.0}
                },
                {
                    "step_id": 2,
                    "action": "rotate",
                    "state": {"x": 1.0, "y": 2.0, "angle": 90.0}
                }
            ],
            "task_description": "Navigate to target"
        }
        
        trace_file = tmp_path / "trace.json"
        with open(trace_file, 'w') as f:
            json.dump(trace_data, f)
        
        result = parse_ale_trace(str(trace_file))
        
        assert isinstance(result, dict)
        assert result["trace_id"] == "test_001"
        assert len(result["steps"]) == 2

    def test_parse_invalid_json(self, tmp_path):
        """Verify error handling for invalid JSON."""
        trace_file = tmp_path / "invalid.json"
        trace_file.write_text("{ invalid json }")
        
        with pytest.raises((json.JSONDecodeError, ValueError)):
            parse_ale_trace(str(trace_file))

    def test_parse_missing_fields(self, tmp_path):
        """Verify handling of missing required fields."""
        trace_data = {
            "steps": []  # Missing trace_id
        }
        
        trace_file = tmp_path / "partial.json"
        with open(trace_file, 'w') as f:
            json.dump(trace_data, f)
        
        # Should handle gracefully or raise appropriate error
        result = parse_ale_trace(str(trace_file))
        assert isinstance(result, dict)

    def test_parse_empty_trace(self, tmp_path):
        """Verify parsing of empty trace."""
        trace_data = {
            "trace_id": "empty_001",
            "steps": [],
            "task_description": ""
        }
        
        trace_file = tmp_path / "empty.json"
        with open(trace_file, 'w') as f:
            json.dump(trace_data, f)
        
        result = parse_ale_trace(str(trace_file))
        assert result["trace_id"] == "empty_001"
        assert result["steps"] == []

    def test_parse_complex_state(self, tmp_path):
        """Verify parsing of complex state structures."""
        trace_data = {
            "trace_id": "complex_001",
            "steps": [
                {
                    "step_id": 1,
                    "action": "complex_action",
                    "state": {
                        "nested": {
                            "value": 1.0,
                            "list": [1, 2, 3]
                        }
                    }
                }
            ],
            "task_description": "Test complex state"
        }
        
        trace_file = tmp_path / "complex.json"
        with open(trace_file, 'w') as f:
            json.dump(trace_data, f)
        
        result = parse_ale_trace(str(trace_file))
        assert len(result["steps"]) == 1
        assert "nested" in result["steps"][0]["state"]
