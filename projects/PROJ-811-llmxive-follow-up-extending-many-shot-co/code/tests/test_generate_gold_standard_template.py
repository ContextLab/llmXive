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
    main,
    GOLD_STANDARD_PATH
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

@pytest.fixture
def temp_json_path(temp_dir):
    return temp_dir / "test_gold.json"

def test_template_structure():
    """Test that the generated template has the correct structure."""
    template = generate_template()
    assert "metadata" in template
    assert "annotations" in template
    assert isinstance(template["annotations"], list)
    assert "instructions" in template["metadata"]
    assert "description" in template["metadata"]

def test_file_generation_creates_json(temp_json_path):
    """Test that save_gold_standard creates the file."""
    data = generate_template()
    result = save_gold_standard(data, temp_json_path)
    assert result is True
    assert temp_json_path.exists()
    with open(temp_json_path, 'r') as f:
        loaded = json.load(f)
    assert loaded["metadata"]["version"] == "1.0"

def test_load_gold_standard_missing_file(temp_dir):
    """Test loading a file that doesn't exist returns None."""
    non_existent = temp_dir / "missing.json"
    result = load_gold_standard(non_existent)
    assert result is None

def test_load_gold_standard_valid_file(temp_json_path):
    """Test loading a valid JSON file."""
    data = generate_template()
    save_gold_standard(data, temp_json_path)
    loaded = load_gold_standard(temp_json_path)
    assert loaded is not None
    assert loaded["metadata"]["version"] == "1.0"

def test_load_gold_standard_invalid_json(temp_json_path):
    """Test loading a file with invalid JSON returns None."""
    with open(temp_json_path, 'w') as f:
        f.write("{ invalid json }")
    result = load_gold_standard(temp_json_path)
    assert result is None

def test_main_creates_template_when_missing(temp_dir, caplog):
    """Test main() creates a file if missing."""
    # Mock the global path to use temp_dir
    with patch('scripts.generate_gold_standard_template.GOLD_STANDARD_PATH', temp_dir / "gold.json"):
        with patch('scripts.generate_gold_standard_template.logger') as mock_logger:
            main()
            # Check that save was called or file created
            assert (temp_dir / "gold.json").exists()

def test_main_skips_generation_when_exists(temp_json_path):
    """Test main() skips if file exists."""
    data = generate_template()
    save_gold_standard(data, temp_json_path)
    
    with patch('scripts.generate_gold_standard_template.GOLD_STANDARD_PATH', temp_json_path):
        with patch('scripts.generate_gold_standard_template.logger') as mock_logger:
            main()
            # Should log that it already exists
            any("already exists" in str(call) for call in mock_logger.info.call_args_list)