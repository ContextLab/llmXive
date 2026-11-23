"""
Unit tests for T025b: generate_translations_log.py
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Adjust path for imports if running standalone, though pytest usually handles this
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.evaluation.generate_translations_log import (
    scan_translation_dirs,
    extract_translation_data,
    aggregate_translations,
    save_translations_log
)

@pytest.fixture
def temp_output_dir():
    """Creates a temporary directory structure mimicking raw_translations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        # Create condition subdirectories
        cond1 = base / "zero_shot_basic"
        cond2 = base / "few_shot_style"
        cond1.mkdir()
        cond2.mkdir()

        # Create mock translation files and metadata for cond1
        t1_data = {"output": "console.log('hello');", "input": "print('hello')"}
        t1_meta = {"seed": 42, "input_id": "entry_001"}
        
        with open(cond1 / "entry_001.json", 'w') as f:
            json.dump(t1_data, f)
        with open(cond1 / "entry_001_metadata.json", 'w') as f:
            json.dump(t1_meta, f)

        # Create a mock file with string output for cond2
        t2_data = "function test() { return true; }"
        t2_meta = {"seed": 123, "input_id": "entry_002"}

        with open(cond2 / "entry_002.json", 'w') as f:
            json.dump(t2_data, f)
        with open(cond2 / "entry_002_metadata.json", 'w') as f:
            json.dump(t2_meta, f)

        yield base

def test_scan_translation_dirs(temp_output_dir):
    """Test that scan_translation_dirs finds condition subdirectories."""
    conditions = scan_translation_dirs(temp_output_dir)
    names = [c[0] for c in conditions]
    
    assert "zero_shot_basic" in names
    assert "few_shot_style" in names
    assert len(conditions) == 2

def test_extract_translation_data_valid(temp_output_dir):
    """Test extraction of valid translation data."""
    cond_dir = temp_output_dir / "zero_shot_basic"
    entries = extract_translation_data("zero_shot_basic", cond_dir)
    
    assert len(entries) == 1
    entry = entries[0]
    
    assert entry['prompt_condition'] == "zero_shot_basic"
    assert entry['seed'] == "42"
    assert entry['input_id'] == "entry_001"
    assert "console.log" in entry['raw_output']
    assert 'timestamp' in entry

def test_extract_translation_data_fallback(temp_output_dir):
    """Test extraction when metadata is missing."""
    # Create a file without metadata
    cond_dir = temp_output_dir / "few_shot_style"
    t_data = "var x = 1;"
    with open(cond_dir / "no_meta.json", 'w') as f:
        json.dump(t_data, f)
    
    entries = extract_translation_data("few_shot_style", cond_dir)
    # Should find the original entry_002 and the new one
    assert len(entries) == 2
    
    no_meta_entry = next(e for e in entries if e['source_file'] == 'no_meta.json')
    assert no_meta_entry['seed'] == "unknown"
    assert no_meta_entry['input_id'] == "unknown"

def test_extract_translation_data_invalid(temp_output_dir):
    """Test handling of invalid JSON files."""
    cond_dir = temp_output_dir / "zero_shot_basic"
    # Create a file with invalid JSON
    with open(cond_dir / "broken.json", 'w') as f:
        f.write("{ invalid json }")
    
    # Should not raise, just log error and skip
    entries = extract_translation_data("zero_shot_basic", cond_dir)
    # Should still have the valid entry
    assert len(entries) >= 1

def test_aggregate_translations_creates_csv(temp_output_dir):
    """Test that aggregate_translations returns all entries."""
    all_entries = aggregate_translations(temp_output_dir)
    assert len(all_entries) == 2
    
    conditions = [e['prompt_condition'] for e in all_entries]
    assert "zero_shot_basic" in conditions
    assert "few_shot_style" in conditions

def test_save_translations_log_creates_csv(temp_output_dir):
    """Test that save_translations_log writes a valid CSV."""
    entries = [
        {
            'prompt_condition': 'test_cond',
            'seed': '1',
            'raw_output': 'code here',
            'timestamp': '2023-01-01',
            'input_id': 'id1',
            'source_file': 'f.json'
        }
    ]
    
    output_path = temp_output_dir / "output.csv"
    save_translations_log(entries, output_path)
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        import csv
        reader = csv.DictReader(f)
        rows = list(reader)
        
    assert len(rows) == 1
    assert rows[0]['prompt_condition'] == 'test_cond'
    assert rows[0]['raw_output'] == 'code here'

def test_save_translations_log_empty(temp_output_dir):
    """Test saving an empty list creates an empty CSV with headers."""
    output_path = temp_output_dir / "empty.csv"
    save_translations_log([], output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        content = f.read()
    
    assert "prompt_condition" in content
    assert len(content.splitlines()) == 1 # Header only