import pytest
import json
import os
import sys
from unittest.mock import patch, MagicMock
import numpy as np

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from save_metrics import validate_metrics_output, load_processed_metrics_schema
from metrics import calculate_birthday_ratio, calculate_consecutive_ratio

class TestValidateMetricsOutput:
    def test_valid_metrics(self):
        schema = {
            "type": "object",
            "required": ["birthday_cluster_ratio", "consecutive_pattern_count"],
            "properties": {
                "birthday_cluster_ratio": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "consecutive_pattern_count": {"type": "number", "minimum": 0.0},
                "is_majority_birthday": {"type": "boolean"},
                "total_draws_processed": {"type": "integer"}
            }
        }
        metrics = {
            "birthday_cluster_ratio": 0.5,
            "consecutive_pattern_count": 0.2,
            "is_majority_birthday": False,
            "total_draws_processed": 100
        }
        errors = validate_metrics_output(metrics, schema)
        assert len(errors) == 0

    def test_missing_required_key(self):
        schema = {
            "type": "object",
            "required": ["birthday_cluster_ratio", "consecutive_pattern_count"],
            "properties": {}
        }
        metrics = {
            "birthday_cluster_ratio": 0.5
        }
        errors = validate_metrics_output(metrics, schema)
        assert "Missing required key: consecutive_pattern_count" in errors

    def test_value_out_of_range(self):
        schema = {
            "type": "object",
            "required": ["birthday_cluster_ratio"],
            "properties": {
                "birthday_cluster_ratio": {"type": "number", "minimum": 0.0, "maximum": 1.0}
            }
        }
        metrics = {
            "birthday_cluster_ratio": 1.5
        }
        errors = validate_metrics_output(metrics, schema)
        assert any("above maximum" in e for e in errors)

    def test_wrong_type(self):
        schema = {
            "type": "object",
            "required": ["is_majority_birthday"],
            "properties": {
                "is_majority_birthday": {"type": "boolean"}
            }
        }
        metrics = {
            "is_majority_birthday": "True"
        }
        errors = validate_metrics_output(metrics, schema)
        assert any("must be a boolean" in e for e in errors)

class TestMetricsCalculation:
    def test_birthday_ratio_all_birthdays(self):
        # All numbers <= 31
        draw = [1, 5, 10, 15, 20, 25]
        ratio = calculate_birthday_ratio(draw)
        assert ratio == 1.0

    def test_birthday_ratio_no_birthdays(self):
        # All numbers > 31
        draw = [32, 33, 34, 35, 36, 37]
        ratio = calculate_birthday_ratio(draw)
        assert ratio == 0.0

    def test_birthday_ratio_mixed(self):
        # 3 birthdays, 3 non-birthdays
        draw = [1, 2, 3, 32, 33, 34]
        ratio = calculate_birthday_ratio(draw)
        assert ratio == 0.5

class TestLoadSchema:
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=MagicMock)
    def test_load_existing_schema(self, mock_open, mock_exists):
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps({"test": "schema"})
        
        schema = load_processed_metrics_schema()
        assert schema == {"test": "schema"}

    @patch('os.path.exists')
    def test_load_missing_schema(self, mock_exists):
        mock_exists.return_value = False
        
        schema = load_processed_metrics_schema()
        assert "required" in schema
        assert "birthday_cluster_ratio" in schema["required"]