"""
Unit tests for generate_translations_log.py
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import csv

# Add project root to path
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.evaluation.generate_translations_log import (
    scan_translation_dirs,
    extract_translation_data,
    aggregate_translations
)

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory structure mimicking data/evaluation/raw_translations"""
    # Create condition directories
    cond_a = tmp_path / "zero_shot_basic"
    cond_b = tmp_path / "few_shot_style"
    cond_a.mkdir()
    cond_b.mkdir()

    # Create mock JSON files
    file_a1 = cond_a / "entry_001.json"
    file_a1.write_text(json.dumps({
        "seed": 42,
        "raw_output": "console.log('hello');",
        "timestamp": "2023-10-01T12:00:00",
        "prompt_condition": "zero_shot_basic"
    }))

    file_b1 = cond_b / "entry_002.json"
    file_b1.write_text(json.dumps({
        "seed": 123,
        "raw_output": "function test() { return 1; }",
        "timestamp": "2023-10-01T12:05:00"
        # Note: missing prompt_condition, should fallback to dir name
    }))

    # Create a corrupted file
    file_corrupt = cond_a / "entry_003.json"
    file_corrupt.write_text("not valid json")

    return tmp_path

def test_scan_translation_dirs(temp_output_dir):
    """Test that the scanner finds all valid JSON files in subdirectories"""
    files = scan_translation_dirs(temp_output_dir)
    
    # Should find 3 files (2 valid, 1 corrupted, but scanner just finds paths)
    # The extraction step filters corruption
    assert len(files) == 3
    
    conditions = [c for c, _ in files]
    assert "zero_shot_basic" in conditions
    assert "few_shot_style" in conditions

def test_extract_translation_data_valid(temp_output_dir):
    """Test extraction from a valid JSON file"""
    json_file = temp_output_dir / "zero_shot_basic" / "entry_001.json"
    data = extract_translation_data("zero_shot_basic", json_file)
    
    assert data is not None
    assert data["prompt_condition"] == "zero_shot_basic"
    assert data["seed"] == 42
    assert data["raw_output"] == "console.log('hello');"
    assert data["timestamp"] == "2023-10-01T12:00:00"

def test_extract_translation_data_fallback(temp_output_dir):
    """Test that missing fields fallback to defaults or directory name"""
    json_file = temp_output_dir / "few_shot_style" / "entry_002.json"
    data = extract_translation_data("few_shot_style", json_file)
    
    assert data is not None
    # Should fallback to directory name since prompt_condition is missing in JSON
    assert data["prompt_condition"] == "few_shot_style"
    assert data["seed"] == 123

def test_extract_translation_data_invalid(temp_output_dir):
    """Test extraction from a corrupted JSON file returns None"""
    json_file = temp_output_dir / "zero_shot_basic" / "entry_003.json"
    data = extract_translation_data("zero_shot_basic", json_file)
    
    assert data is None

def test_aggregate_translations_creates_csv(temp_output_dir):
    """Test the full aggregation pipeline creates a valid CSV"""
    # Mock the base directory to point to our temp dir
    with patch('src.evaluation.generate_translations_log.BASE_OUTPUT_DIR', temp_output_dir):
        with patch('src.evaluation.generate_translations_log.LOG_OUTPUT_FILE', temp_output_dir / "output_log.csv"):
            count = aggregate_translations()
            
            # Should have processed 2 valid entries (1 corrupted skipped)
            assert count == 2
            
            csv_path = temp_output_dir / "output_log.csv"
            assert csv_path.exists()
            
            with open(csv_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                assert len(rows) == 2
                # Verify headers
                assert "prompt_condition" in rows[0]
                assert "seed" in rows[0]
                assert "raw_output" in rows[0]
                assert "timestamp" in rows[0]
                
                # Check specific values
                zero_shot_row = next(r for r in rows if r["seed"] == "42")
                assert zero_shot_row["raw_output"] == "console.log('hello');"