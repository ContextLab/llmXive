"""
Unit tests for verify_human_labels.py logic.
These tests mock the dataset loading to verify the logic without hitting the network.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Import the functions we want to test
# We import the logic directly, but since it's a script, we might need to wrap it
# or import the specific functions if they were separated. 
# For this task, we assume the logic is in the script. 
# To test effectively, we will re-implement the core logic in a helper or import the module.
# Since the task asks for the script, we will test the script's behavior via mocking.

import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from data.verify_human_labels import verify_labels, THRESHOLD_FRACTION

class MockDatasetIterator:
    def __init__(self, data):
        self.data = data
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.index >= len(self.data):
            raise StopIteration
        item = self.data[self.index]
        self.index += 1
        return item

@pytest.fixture
def valid_data():
    """Data where 0% are invalid."""
    return [{"human_verified_label": True}, {"human_verified_label": False}]

@pytest.fixture
def invalid_data_low():
    """Data where 2% are invalid (pass)."""
    # 2 invalid out of 100
    data = [{"human_verified_label": True} for _ in range(98)]
    data.append({"human_verified_label": None})
    data.append({"human_verified_label": "string"})
    return data

@pytest.fixture
def invalid_data_high():
    """Data where 10% are invalid (fail)."""
    # 10 invalid out of 100
    data = [{"human_verified_label": True} for _ in range(90)]
    for _ in range(10):
        data.append({"human_verified_label": None})
    return data

def test_verify_all_valid(valid_data):
    mock_dataset = MockDatasetIterator(valid_data)
    total, invalid, is_valid = verify_labels(mock_dataset)
    assert total == 2
    assert invalid == 0
    assert is_valid is True

def test_verify_low_invalid_pass(invalid_data_low):
    mock_dataset = MockDatasetIterator(invalid_data_low)
    total, invalid, is_valid = verify_labels(mock_dataset)
    assert total == 100
    assert invalid == 2
    assert is_valid is True  # 2% < 5%

def test_verify_high_invalid_fail(invalid_data_high):
    mock_dataset = MockDatasetIterator(invalid_data_high)
    total, invalid, is_valid = verify_labels(mock_dataset)
    assert total == 100
    assert invalid == 10
    assert is_valid is False  # 10% > 5%

def test_verify_edge_case_boundary():
    """Test exactly 5% invalid."""
    # 5 invalid out of 100 -> 5% -> should PASS (<= 5%)
    data = [{"human_verified_label": True} for _ in range(95)]
    data.extend([{"human_verified_label": None}] * 5)
    mock_dataset = MockDatasetIterator(data)
    total, invalid, is_valid = verify_labels(mock_dataset)
    assert invalid == 5
    assert is_valid is True

def test_verify_edge_case_boundary_plus_one():
    """Test 5.01% invalid (6 out of 100)."""
    data = [{"human_verified_label": True} for _ in range(94)]
    data.extend([{"human_verified_label": None}] * 6)
    mock_dataset = MockDatasetIterator(data)
    total, invalid, is_valid = verify_labels(mock_dataset)
    assert invalid == 6
    assert is_valid is False