"""
Tests for T012c: Generate static test fixture from real data.

This module tests the generation of data/test_static_logs.json
ensuring it contains the required columns and is valid JSON.
"""
import json
import os
import sys
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_path


def test_static_fixture_file_exists():
    """Test that the static fixture file exists after generation."""
    data_path = get_path("data")
    fixture_file = data_path / "test_static_logs.json"
    
    assert fixture_file.exists(), f"Static fixture file not found: {fixture_file}"
    assert fixture_file.stat().st_size > 0, "Static fixture file is empty"


def test_static_fixture_is_valid_json():
    """Test that the static fixture file contains valid JSON."""
    data_path = get_path("data")
    fixture_file = data_path / "test_static_logs.json"
    
    try:
        with open(fixture_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert isinstance(data, list), "Fixture data should be a list"
    except json.JSONDecodeError as e:
        pytest.fail(f"Static fixture is not valid JSON: {e}")


def test_static_fixture_has_required_columns():
    """Test that each entry has log_id, text, and label columns."""
    data_path = get_path("data")
    fixture_file = data_path / "test_static_logs.json"
    
    with open(fixture_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert len(data) > 0, "Fixture should contain at least one entry"
    
    required_columns = {'log_id', 'text', 'label'}
    for i, entry in enumerate(data):
        assert isinstance(entry, dict), f"Entry {i} should be a dictionary"
        assert required_columns.issubset(entry.keys()), \
            f"Entry {i} missing required columns: {required_columns - set(entry.keys())}"


def test_static_fixture_log_ids_are_strings():
    """Test that log_id values are strings."""
    data_path = get_path("data")
    fixture_file = data_path / "test_static_logs.json"
    
    with open(fixture_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for i, entry in enumerate(data):
        assert isinstance(entry['log_id'], str), \
            f"Entry {i} log_id should be a string, got {type(entry['log_id'])}"


def test_static_fixture_text_are_strings():
    """Test that text values are strings."""
    data_path = get_path("data")
    fixture_file = data_path / "test_static_logs.json"
    
    with open(fixture_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for i, entry in enumerate(data):
        assert isinstance(entry['text'], str), \
            f"Entry {i} text should be a string, got {type(entry['text'])}"
        assert len(entry['text']) > 0, f"Entry {i} text should not be empty"


def test_static_fixture_labels_are_valid():
    """Test that label values are valid (jailbreak or safe)."""
    data_path = get_path("data")
    fixture_file = data_path / "test_static_logs.json"
    
    with open(fixture_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    valid_labels = {'jailbreak', 'safe'}
    for i, entry in enumerate(data):
        assert entry['label'] in valid_labels, \
            f"Entry {i} has invalid label: {entry['label']}. Expected one of {valid_labels}"


def test_static_fixture_has_both_label_types():
    """Test that fixture contains both attack and benign samples."""
    data_path = get_path("data")
    fixture_file = data_path / "test_static_logs.json"
    
    with open(fixture_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    labels = {entry['label'] for entry in data}
    assert 'jailbreak' in labels, "Fixture should contain jailbreak samples"
    assert 'safe' in labels, "Fixture should contain safe samples"