"""
Unit tests for download_diverse_prompts.py
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import csv
import tempfile

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config import Config
from code.data.download_diverse_prompts import (
    fetch_diverse_prompts,
    load_coco_captions,
    merge_and_deduplicate,
    write_merged_csv
)

@pytest.fixture
def mock_dataset_item():
    return {
        "prompt": "A beautiful sunset over the mountains.",
        "other_field": "ignored"
    }

@pytest.fixture
def mock_dataset_stream(mock_dataset_item):
    # Create an iterator that yields items then stops
    items = [mock_dataset_item] * 10
    return iter(items)

def test_fetch_diverse_prompts_success():
    """Test successful fetching of prompts from a mocked dataset."""
    mock_dataset = MagicMock()
    mock_dataset.__iter__ = lambda self: iter([{"prompt": "Test prompt 1"}, {"prompt": "Test prompt 2"}])
    
    with patch('code.data.download_diverse_prompts.load_dataset', return_value=mock_dataset):
        prompts = fetch_diverse_prompts(
            source="test/source",
            column="prompt",
            split="train",
            sample_size=2,
            seed=42
        )
    
    assert len(prompts) == 2
    assert "Test prompt 1" in prompts
    assert "Test prompt 2" in prompts

def test_fetch_diverse_prompts_empty_raises():
    """Test that fetching from an empty dataset raises an error."""
    mock_dataset = MagicMock()
    mock_dataset.__iter__ = lambda self: iter([])
    
    with patch('code.data.download_diverse_prompts.load_dataset', return_value=mock_dataset):
        with pytest.raises(RuntimeError, match="No valid prompts found"):
            fetch_diverse_prompts(
                source="test/source",
                column="prompt",
                split="train",
                sample_size=1,
                seed=42
            )

def test_merge_and_deduplicate():
    """Test merging and deduplication logic."""
    existing = [
        {"source": "ms_coco", "text": "A cat"},
        {"source": "ms_coco", "text": "A dog"}
    ]
    new_prompts = [
        "A cat",  # Duplicate
        "A bird", # New
        "A fish"  # New
    ]
    
    merged = merge_and_deduplicate(existing, new_prompts)
    
    assert len(merged) == 4 # 2 existing + 2 new
    sources = [m["source"] for m in merged]
    assert sources.count("ms_coco") == 2
    assert sources.count("diverse_external") == 2

def test_write_merged_csv():
    """Test writing merged data to CSV."""
    data = [
        {"source": "ms_coco", "text": "Test 1"},
        {"source": "diverse", "text": "Test 2"}
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.csv"
        write_merged_csv(data, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        assert rows[0]['source'] == 'ms_coco'
        assert rows[0]['prompt'] == 'Test 1'
        assert rows[1]['source'] == 'diverse'
        assert rows[1]['prompt'] == 'Test 2'