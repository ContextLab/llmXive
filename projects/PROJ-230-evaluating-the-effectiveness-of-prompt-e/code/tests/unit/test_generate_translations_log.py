"""
Unit tests for src/evaluation/generate_translations_log.py
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from src.evaluation.generate_translations_log import (
    scan_translation_dirs,
    extract_translation_data,
    aggregate_translations
)

@pytest.fixture
def temp_output_dir():
    """Creates a temporary directory structure simulating raw_translations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        # Create condition directories
        cond1 = base / "zero_shot_basic"
        cond2 = base / "few_shot_style"
        cond1.mkdir()
        cond2.mkdir()

        # Create valid JSON files
        valid_data_1 = {
            "condition": "zero_shot_basic",
            "seed": 42,
            "output_code": "console.log('hello');",
            "timestamp": "2023-10-27T10:00:00Z"
        }
        valid_data_2 = {
            "condition": "few_shot_style",
            "seed": 123,
            "output_code": "function add(a, b) { return a + b; }",
            "timestamp": "2023-10-27T10:05:00Z"
        }

        (cond1 / "entry_001.json").write_text(json.dumps(valid_data_1))
        (cond2 / "entry_002.json").write_text(json.dumps(valid_data_2))

        # Create a corrupted file
        (cond1 / "corrupted.json").write_text("not valid json {{{")

        yield base

def test_scan_translation_dirs(temp_output_dir):
    """Test that scan_translation_dirs finds all JSON files in subdirectories."""
    files = scan_translation_dirs(temp_output_dir)
    # Should find 3 files: 2 valid, 1 corrupted
    assert len(files) == 3
    # Verify they are in the expected directories
    dirs = [f.parent.name for f in files]
    assert "zero_shot_basic" in dirs
    assert "few_shot_style" in dirs

def test_extract_translation_data_valid(temp_output_dir):
    """Test extraction from a valid JSON file."""
    json_path = temp_output_dir / "zero_shot_basic" / "entry_001.json"
    record = extract_translation_data(json_path)

    assert record is not None
    assert record["prompt_condition"] == "zero_shot_basic"
    assert record["seed"] == 42
    assert record["raw_output"] == "console.log('hello');"
    assert record["timestamp"] == "2023-10-27T10:00:00Z"

def test_extract_translation_data_fallback(temp_output_dir):
    """Test extraction when condition key is missing (fallback to dirname)."""
    # Create a file without 'condition' key
    bad_data = {
        "seed": 99,
        "output_code": "test",
        "timestamp": "2023-01-01"
    }
    path = temp_output_dir / "zero_shot_basic" / "fallback_test.json"
    path.write_text(json.dumps(bad_data))

    record = extract_translation_data(path)
    assert record is not None
    assert record["prompt_condition"] == "zero_shot_basic" # Should fallback to dirname

def test_extract_translation_data_invalid(temp_output_dir):
    """Test extraction from a corrupted JSON file."""
    json_path = temp_output_dir / "zero_shot_basic" / "corrupted.json"
    record = extract_translation_data(json_path)
    assert record is None

def test_aggregate_translations_creates_csv(temp_output_dir):
    """Test that aggregate_translations creates a CSV with correct headers and rows."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "translations_log.csv"

        aggregate_translations(temp_output_dir, output_path)

        assert output_path.exists()
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Should have 2 valid rows (corrupted one skipped)
        assert len(rows) == 2

        # Check headers
        assert set(rows[0].keys()) == {"prompt_condition", "seed", "raw_output", "timestamp"}

        # Check content of one row
        conditions = [r["prompt_condition"] for r in rows]
        assert "zero_shot_basic" in conditions
        assert "few_shot_style" in conditions
