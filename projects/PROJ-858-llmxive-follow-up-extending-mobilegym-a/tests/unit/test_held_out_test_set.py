import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from scheduler.generate_held_out_test_set import (
    extract_training_variables,
    extract_schema_variables,
    generate_held_out_set
)

class TestHeldOutTestSetGeneration:
    """Unit tests for T029: Held-out test set generation."""

    def test_extract_training_variables_from_list_format(self, tmp_path):
        """Test extraction from list-based coverage vectors format."""
        # Create mock coverage vectors file
        mock_data = [
            {
                "app_id": "app1",
                "vector": {
                    "dark_mode": True,
                    "unread_count": 5,
                    "battery_low": False
                }
            },
            {
                "app_id": "app2",
                "vector": {
                    "dark_mode": False,
                    "wifi_connected": True,
                    "volume_level": 3
                }
            }
        ]
        
        test_file = tmp_path / "coverage_vectors.json"
        with open(test_file, 'w') as f:
            json.dump(mock_data, f)
        
        result = extract_training_variables(str(test_file))
        
        expected = {"dark_mode", "unread_count", "battery_low", "wifi_connected", "volume_level"}
        assert result == expected, f"Expected {expected}, got {result}"

    def test_extract_training_variables_from_dict_format(self, tmp_path):
        """Test extraction from dict-based coverage vectors format."""
        mock_data = {
            "app1": {
                "vector": {
                    "dark_mode": True,
                    "battery_low": False
                }
            },
            "app2": {
                "state_vector": {
                    "wifi_connected": True,
                    "volume_level": 3
                }
            }
        }
        
        test_file = tmp_path / "coverage_vectors.json"
        with open(test_file, 'w') as f:
            json.dump(mock_data, f)
        
        result = extract_training_variables(str(test_file))
        
        expected = {"dark_mode", "battery_low", "wifi_connected", "volume_level"}
        assert result == expected, f"Expected {expected}, got {result}"

    def test_generate_held_out_set_with_overlap(self):
        """Test held-out generation when some variables overlap."""
        training_vars = {"dark_mode", "unread_count", "battery_low"}
        schema_vars = {"dark_mode", "unread_count", "battery_low", "wifi_connected", "volume_level"}
        
        result = generate_held_out_set(training_vars, schema_vars)
        
        assert "held_out_variables" in result
        assert "training_variables" in result
        assert "metadata" in result
        
        expected_held_out = {"wifi_connected", "volume_level"}
        assert set(result["held_out_variables"]) == expected_held_out
        
        # Check metadata
        assert result["metadata"]["total_schema_variables"] == 5
        assert result["metadata"]["training_variables_count"] == 3
        assert result["metadata"]["held_out_variables_count"] == 2

    def test_generate_held_out_set_no_overlap(self):
        """Test held-out generation when no variables overlap."""
        training_vars = {"dark_mode", "unread_count"}
        schema_vars = {"wifi_connected", "volume_level", "battery_low"}
        
        result = generate_held_out_set(training_vars, schema_vars)
        
        expected_held_out = {"wifi_connected", "volume_level", "battery_low"}
        assert set(result["held_out_variables"]) == expected_held_out
        assert result["metadata"]["held_out_variables_count"] == 3

    def test_generate_held_out_set_all_covered(self):
        """Test held-out generation when all schema variables are in training."""
        training_vars = {"dark_mode", "unread_count", "battery_low"}
        schema_vars = {"dark_mode", "unread_count", "battery_low"}
        
        result = generate_held_out_set(training_vars, schema_vars)
        
        assert result["held_out_variables"] == []
        assert result["metadata"]["held_out_variables_count"] == 0

    def test_metadata_contains_required_fields(self):
        """Verify metadata contains all required FR-005 fields."""
        training_vars = {"dark_mode"}
        schema_vars = {"dark_mode", "wifi_connected"}
        
        result = generate_held_out_set(training_vars, schema_vars)
        
        metadata = result["metadata"]
        assert "generated_at" in metadata
        assert "total_schema_variables" in metadata
        assert "training_variables_count" in metadata
        assert "held_out_variables_count" in metadata
        assert "purpose" in metadata
        assert "description" in metadata
        
        assert "FR-005" in metadata["purpose"]
        assert "transfer" in metadata["description"].lower()

    def test_extract_schema_variables_fallback(self):
        """Test schema variable extraction with constants fallback."""
        with patch('scheduler.generate_held_out_test_set.get_semantic_proxies') as mock_proxies:
            mock_proxies.return_value = ["dark_mode", "wifi_connected", "battery_low"]
            
            result = extract_schema_variables()
            
            assert result == {"dark_mode", "wifi_connected", "battery_low"}
            mock_proxies.assert_called_once()

    def test_held_out_set_is_valid_json(self, tmp_path):
        """Verify the generated held-out set is valid JSON and can be reloaded."""
        training_vars = {"dark_mode", "unread_count"}
        schema_vars = {"dark_mode", "unread_count", "wifi_connected", "volume_level"}
        
        result = generate_held_out_set(training_vars, schema_vars)
        
        # Should be serializable
        json_str = json.dumps(result)
        reloaded = json.loads(json_str)
        
        assert reloaded == result
        assert set(reloaded["held_out_variables"]) == {"wifi_connected", "volume_level"}