"""
Unit tests for code/config.py dataset selection and validation.
"""
import pytest
from code.config import DATASET_LIST, validate_dataset_counts

def test_dataset_list_length():
    assert len(DATASET_LIST) == 10, "Must have exactly 10 datasets"

def test_dataset_types_distribution():
    counts = {"continuous": 0, "count": 0, "binary": 0}
    for ds in DATASET_LIST:
        counts[ds["outcome_type"]] += 1
    
    assert counts["continuous"] == 3
    assert counts["count"] == 3
    assert counts["binary"] == 4

def test_validate_dataset_counts():
    assert validate_dataset_counts() is True

def test_dataset_structure():
    required_keys = {"id", "name", "url", "outcome_type", "description", "source"}
    for ds in DATASET_LIST:
        assert set(ds.keys()) == required_keys, f"Missing keys in dataset: {ds['name']}"
        assert ds["outcome_type"] in ["continuous", "count", "binary"]
        assert ds["id"].isdigit()
        assert ds["url"].startswith("https://")
