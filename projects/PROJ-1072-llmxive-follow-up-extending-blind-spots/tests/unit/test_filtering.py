import pytest
from code.utils.filtering_utils import is_valid_category, filter_by_categories

def test_is_valid_category_positive():
    assert is_valid_category("Abstract Reasoning", {"Abstract Reasoning", "Object-Centric"}) is True
    assert is_valid_category("Object-Centric", {"Abstract Reasoning", "Object-Centric"}) is True

def test_is_valid_category_negative():
    assert is_valid_category("Perceptual", {"Abstract Reasoning", "Object-Centric"}) is False
    assert is_valid_category("", {"Abstract Reasoning", "Object-Centric"}) is False
    assert is_valid_category(None, {"Abstract Reasoning", "Object-Centric"}) is False

def test_filter_by_categories():
    records = [
        {"task_id": "1", "category": "Abstract Reasoning"},
        {"task_id": "2", "category": "Object-Centric"},
        {"task_id": "3", "category": "Perceptual"},
        {"task_id": "4", "category": "Procedural"},
    ]
    valid_cats = {"Abstract Reasoning", "Object-Centric"}
    filtered = filter_by_categories(records, valid_cats)
    
    assert len(filtered) == 2
    assert filtered[0]["task_id"] == "1"
    assert filtered[1]["task_id"] == "2"
