"""
Tests for the generate_gold_standard_template script.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.generate_gold_standard_template import (
    generate_template,
    load_gold_standard,
    save_gold_standard,
    main
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_json_path(temp_dir):
    """Create a temporary JSON file path."""
    return temp_dir / "test_gold_standard.json"


def test_template_structure():
    """Test that the generated template has the correct structure."""
    template = generate_template(num_entries=5)
    
    assert "version" in template
    assert "description" in template
    assert "note" in template
    assert "entries" in template
    assert isinstance(template["entries"], list)
    assert len(template["entries"]) == 5
    
    # Check entry structure
    for entry in template["entries"]:
        assert "id" in entry
        assert "human_complexity_score" in entry
        assert "notes" in entry
        assert "metadata" in entry
        assert 1 <= entry["human_complexity_score"] <= 5


def test_file_generation_creates_json(temp_dir, temp_json_path):
    """Test that saving the template creates the JSON file."""
    template = generate_template(num_entries=3)
    save_gold_standard(template, temp_json_path)
    
    assert temp_json_path.exists()
    
    with open(temp_json_path, 'r') as f:
        loaded = json.load(f)
        
    assert loaded == template


def test_load_gold_standard_missing_file(temp_dir):
    """Test loading a non-existent file returns None."""
    non_existent = temp_dir / "non_existent.json"
    result = load_gold_standard(non_existent)
    assert result is None


def test_load_gold_standard_valid_file(temp_dir, temp_json_path):
    """Test loading a valid JSON file."""
    template = generate_template(num_entries=3)
    save_gold_standard(template, temp_json_path)
    
    loaded = load_gold_standard(temp_json_path)
    assert loaded == template


def test_load_gold_standard_invalid_json(temp_dir, temp_json_path):
    """Test loading an invalid JSON file raises an error."""
    with open(temp_json_path, 'w') as f:
        f.write("not valid json")
        
    with pytest.raises(json.JSONDecodeError):
        load_gold_standard(temp_json_path)


def test_main_creates_template_when_missing(temp_dir):
    """Test that main() creates the template when it doesn't exist."""
    target_path = temp_dir / "gold_standard.json"
    
    with patch('scripts.generate_gold_standard_template.GOLD_STANDARD_PATH', target_path):
        result = main()
        
    assert result == 0
    assert target_path.exists()
    
    with open(target_path, 'r') as f:
        data = json.load(f)
        
    assert "entries" in data
    assert len(data["entries"]) > 0


def test_main_skips_generation_when_exists(temp_dir):
    """Test that main() skips generation if the file already exists."""
    target_path = temp_dir / "gold_standard.json"
    
    # Create the file first
    target_path.touch()
    
    with patch('scripts.generate_gold_standard_template.GOLD_STANDARD_PATH', target_path):
        result = main()
        
    assert result == 0
    # File should still exist and be unchanged (empty or with original content)
    assert target_path.exists()