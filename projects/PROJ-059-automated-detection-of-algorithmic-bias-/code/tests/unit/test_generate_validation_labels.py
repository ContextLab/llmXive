"""
Unit tests for the generate_validation_labels script.

Tests:
1. Deterministic_heuristic consistency (same input -> same output).
2. CSV structure validation.
3. Error handling simulation (mocking fetch failure).
"""
import pytest
import sys
import os
import csv
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import random

# Add the project root to the path if running from tests
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.generate_validation_labels import (
    apply_deterministic_heuristic,
    write_labels_csv,
    fetch_real_data,
    RANDOM_SEED,
    SAMPLE_SIZE
)

class TestDeterministicHeuristic:
    def test_same_text_same_label(self):
        """Ensure the heuristic is deterministic for the same input text."""
        text = "This is a test comment about bias."
        result1 = apply_deterministic_heuristic({"text": text})
        result2 = apply_deterministic_heuristic({"text": text})
        
        assert result1["label"] == result2["label"]
        assert result1["confidence"] == result2["confidence"]
    
    def test_different_text_different_label_possibility(self):
        """Ensure different texts can yield different labels."""
        text1 = "This is a test comment about bias."
        text2 = "This is a completely different neutral comment."
        
        result1 = apply_deterministic_heuristic({"text": text1})
        result2 = apply_deterministic_heuristic({"text": text2})
        
        # We don't assert they MUST be different (due to randomness in heuristic),
        # but we assert the structure is correct.
        assert "label" in result1
        assert "label" in result2
        assert result1["label"] in [0, 1]
        assert result2["label"] in [0, 1]

class TestWriteLabelsCsv:
    def test_csv_structure(self):
        """Test that the CSV file is written with correct headers and data."""
        data = [
            {"text": "test1", "label": 1, "confidence": 0.9, "source": "test"},
            {"text": "test2", "label": 0, "confidence": 0.8, "source": "test"}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "labels.csv"
            write_labels_csv(data, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                assert len(rows) == 2
                assert "text" in rows[0]
                assert "label" in rows[0]
                assert "confidence" in rows[0]
                assert "source" in rows[0]

class TestFetchRealData:
    @patch('scripts.generate_validation_labels.load_dataset')
    def test_fetch_success(self, mock_load_dataset):
        """Test successful data fetch."""
        # Mock dataset iterator
        mock_iter = [
            {"text": "sample 1"},
            {"text": "sample 2"},
            {"text": "sample 3"}
        ]
        mock_ds = MagicMock()
        mock_ds.__iter__ = MagicMock(return_value=iter(mock_iter))
        mock_load_dataset.return_value = mock_ds
        
        result = fetch_real_data()
        
        assert len(result) == 3
        assert all("text" in item for item in result)
    
    @patch('scripts.generate_validation_labels.load_dataset')
    def test_fetch_failure_raises_error(self, mock_load_dataset):
        """Test that fetch failure raises a RuntimeError."""
        mock_load_dataset.side_effect = Exception("Dataset not found")
        
        with pytest.raises(RuntimeError, match="CRITICAL: Failed to fetch real data"):
            fetch_real_data()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])