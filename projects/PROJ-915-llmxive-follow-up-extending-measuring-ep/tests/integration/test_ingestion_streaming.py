"""
Integration test for T049: Streaming Large Dataset Processing.
Verifies that ingestion.py correctly uses streaming mode and handles chunking.
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.ingestion import load_and_filter_dataset, validate_schema, save_to_csv
from code.error_handling import DatasetDownloadError

class MockDatasetItem:
    """Mock dataset item generator."""
    def __init__(self, count=150):
        self.count = count
        self.index = 0
        
    def __iter__(self):
        return self
        
    def __next__(self):
        if self.index >= self.count:
            raise StopIteration
        
        item = {
            "id": f"mock_{self.index}",
            "prompt": f"This is a mock prompt {self.index} with authority-framed content.",
            "label": "Authority-framed",
            "false_claim": f"False claim {self.index}"
        }
        self.index += 1
        return item

def test_load_and_filter_dataset_streaming():
    """Test that the dataset loader uses streaming and filters correctly."""
    # Mock the load_dataset function to return our mock data
    mock_dataset = MockDatasetItem(count=150)
    
    with patch('code.ingestion.load_dataset', return_value=mock_dataset):
        # Use streaming=True explicitly
        items = list(load_and_filter_dataset(streaming=True))
        
        # We expect 150 items because all are "Authority-framed"
        assert len(items) == 150
        
        # Verify the first item structure
        assert "id" in items[0]
        assert "prompt" in items[0]
        assert "false_claim" in items[0]

def test_validate_schema_missing_claim():
    """Test schema validation when false_claim is missing but extractable."""
    item = {
        "id": "test_1",
        "prompt": "false_claim: 'This is a fake claim' in the text."
    }
    
    is_valid, error = validate_schema(item)
    
    assert is_valid is True
    assert "false_claim" in item  # Should have been added
    assert item["false_claim"] == "This is a fake claim"

def test_validate_schema_invalid():
    """Test schema validation when required fields are missing."""
    item = {
        "prompt": "Some text"
        # Missing "id"
    }
    
    is_valid, error = validate_schema(item)
    
    assert is_valid is False
    assert "Missing required field: id" in error

def test_save_to_csv_creates_file():
    """Test that save_to_csv actually writes a file."""
    data = [
        {"id": "1", "prompt": "Test 1", "false_claim": "Claim 1"},
        {"id": "2", "prompt": "Test 2", "false_claim": "Claim 2"}
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.csv"
        save_to_csv(data, output_path)
        
        assert output_path.exists()
        
        # Read back and verify
        with open(output_path, "r") as f:
            content = f.read()
            
        assert "id" in content
        assert "Test 1" in content
        assert "Claim 1" in content

def test_streaming_memory_efficiency():
    """
    Verify that the generator yields items one by one (conceptually).
    In a real scenario, this prevents loading the whole dataset into memory.
    """
    mock_dataset = MockDatasetItem(count=50)
    
    with patch('code.ingestion.load_dataset', return_value=mock_dataset):
        generator = load_and_filter_dataset(streaming=True)
        
        # Consume one by one
        first = next(generator)
        assert first["id"] == "mock_0"
        
        second = next(generator)
        assert second["id"] == "mock_1"
        
        # Verify it's a generator and not a list
        import types
        assert isinstance(generator, types.GeneratorType)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])