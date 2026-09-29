import os
import sys
import csv
import tempfile
from pathlib import Path
from unittest import mock
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.download_diverse_prompts import (
    fetch_diverse_prompts,
    load_coco_captions,
    merge_and_deduplicate,
    write_merged_csv
)
from config import Config

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_merge_and_deduplicate():
    """Test that merge_and_deduplicate removes exact duplicates."""
    coco = [{'prompt': 'A cat', 'source': 'coco'}]
    diverse = [{'prompt': 'A cat', 'source': 'hf'}, {'prompt': 'A dog', 'source': 'hf'}]
    result = merge_and_deduplicate(coco, diverse)
    assert len(result) == 2
    prompts = [p['prompt'] for p in result]
    assert 'A cat' in prompts
    assert 'A dog' in prompts

def test_write_merged_csv(temp_dir):
    """Test that write_merged_csv creates a valid CSV."""
    prompts = [
        {'prompt': 'Hello World', 'source': 'test'},
        {'prompt': 'Line\nBreak', 'source': 'test'}
    ]
    output_path = temp_dir / "test.csv"
    write_merged_csv(prompts, output_path)
    assert output_path.exists()
    with open(output_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 2
    assert rows[0]['prompt'] == 'Hello World'
    assert rows[1]['prompt'] == 'Line Break'  # Newlines replaced

@mock.patch('data.download_diverse_prompts.load_dataset')
def test_fetch_diverse_prompts(mock_load_dataset):
    """Test fetch_diverse_prompts with mocked dataset."""
    mock_dataset = [
        {'caption': 'Image 1'},
        {'caption': 'Image 2'},
        {'caption': None},  # Should be skipped
        {'caption': 'Image 3'}
    ]
    mock_load_dataset.return_value = mock_dataset

    result = fetch_diverse_prompts()
    assert len(result) == 3
    assert all('prompt' in item for item in result)
    assert all('source' in item for item in result)

def test_load_coco_captions_missing_file(temp_dir):
    """Test that load_coco_captions fails if file is missing."""
    config = Config()
    # Override data_path to temp dir to ensure isolation
    config.data_path = temp_dir
    with pytest.raises(FileNotFoundError):
        load_coco_captions(config)

def test_load_coco_captions_success(temp_dir):
    """Test load_coco_captions with valid file."""
    # Create the expected file structure
    processed_dir = temp_dir / "processed"
    processed_dir.mkdir()
    coco_file = processed_dir / "prompts_test.csv"
    
    with open(coco_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['caption'])
        writer.writeheader()
        writer.writerow({'caption': 'Test Caption'})
        
    config = Config()
    config.data_path = temp_dir
    
    result = load_coco_captions(config)
    assert len(result) == 1
    assert result[0]['prompt'] == 'Test Caption'
    assert result[0]['source'] == 'ms-coco-validation'