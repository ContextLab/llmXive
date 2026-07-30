"""
Unit tests for T013: save_metrics.py
Tests schema validation and file saving logic.
"""
import pytest
import json
import os
import tempfile
import sys
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from exceptions import LotteryDataError
from code.save_metrics import validate_metrics_schema

@pytest.fixture
def valid_metrics_data():
    return {
        "total_draws": 1,
        "draws_with_sales_data": 1,
        "draws_without_sales_data": 0,
        "metrics": [
            {
                "draw_index": 0,
                "draw_date": "2023-01-01",
                "numbers": [1, 2, 3, 4, 5, 6],
                "birthday_cluster_ratio": 1.0,
                "consecutive_pattern_count": 1.0,
                "is_majority_birthday": True,
                "jackpot_amount": 5000000,
                "has_sales_data": True,
                "total_sales": 15000000
            }
        ]
    }

def test_validate_valid_schema(valid_metrics_data):
    """Test that a valid schema passes validation."""
    assert validate_metrics_schema(valid_metrics_data) is True

def test_validate_missing_top_level_key(valid_metrics_data):
    """Test that missing top-level keys raise an error."""
    del valid_metrics_data['total_draws']
    with pytest.raises(LotteryDataError, match="Missing required top-level key: total_draws"):
        validate_metrics_schema(valid_metrics_data)

def test_validate_metrics_not_list(valid_metrics_data):
    """Test that metrics must be a list."""
    valid_metrics_data['metrics'] = "not a list"
    with pytest.raises(LotteryDataError, match="Field 'metrics' must be a list"):
        validate_metrics_schema(valid_metrics_data)

def test_validate_missing_metric_field(valid_metrics_data):
    """Test that missing fields in metric items raise an error."""
    del valid_metrics_data['metrics'][0]['draw_date']
    with pytest.raises(LotteryDataError, match="Missing required field in metric item: draw_date"):
        validate_metrics_schema(valid_metrics_data)

def test_validate_empty_metrics_list(valid_metrics_data):
    """Test that an empty metrics list is valid (no sample to check fields)."""
    valid_metrics_data['metrics'] = []
    assert validate_metrics_schema(valid_metrics_data) is True