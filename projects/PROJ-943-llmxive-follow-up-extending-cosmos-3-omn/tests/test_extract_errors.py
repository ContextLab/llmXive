import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.extract_errors import (
    load_predictions,
    extract_misclassified,
    save_misclassified,
    INPUT_PATH,
    OUTPUT_PATH
)

class TestExtractErrors:
    
    def test_load_predictions_valid_file(self, tmp_path):
        """Test loading a valid JSONL file."""
        input_file = tmp_path / "predictions.jsonl"
        data = [
            {"id": 1, "true_label": "A", "predicted_label": "A"},
            {"id": 2, "true_label": "B", "predicted_label": "C"},
            {"id": 3, "true_label": "D", "predicted_label": "D"}
        ]
        with open(input_file, 'w') as f:
            for item in data:
                f.write(json.dumps(item) + '\n')
        
        result = load_predictions(input_file)
        assert len(result) == 3
        assert result[0]['id'] == 1

    def test_load_predictions_missing_file(self, tmp_path):
        """Test that loading a missing file raises FileNotFoundError."""
        non_existent = tmp_path / "does_not_exist.jsonl"
        with pytest.raises(FileNotFoundError):
            load_predictions(non_existent)

    def test_extract_misclassified_logic(self):
        """Test the core logic of identifying misclassified samples."""
        predictions = [
            {"id": 1, "true_label": "cat", "predicted_label": "cat"},
            {"id": 2, "true_label": "dog", "predicted_label": "bird"},
            {"id": 3, "true_label": "car", "predicted_label": "truck"},
            {"id": 4, "true_label": "tree", "predicted_label": "tree"},
            {"id": 5, "true_label": "sky", "predicted_label": "grass"}
        ]
        
        misclassified = extract_misclassified(predictions)
        
        assert len(misclassified) == 3
        ids = [m['id'] for m in misclassified]
        assert 2 in ids
        assert 3 in ids
        assert 5 in ids
        assert 1 not in ids
        assert 4 not in ids

    def test_extract_misclassified_all_correct(self):
        """Test when all predictions are correct."""
        predictions = [
            {"id": 1, "true_label": "A", "predicted_label": "A"},
            {"id": 2, "true_label": "B", "predicted_label": "B"}
        ]
        misclassified = extract_misclassified(predictions)
        assert len(misclassified) == 0

    def test_extract_misclassified_all_wrong(self):
        """Test when all predictions are wrong."""
        predictions = [
            {"id": 1, "true_label": "A", "predicted_label": "B"},
            {"id": 2, "true_label": "C", "predicted_label": "D"}
        ]
        misclassified = extract_misclassified(predictions)
        assert len(misclassified) == 2

    def test_extract_misclassified_missing_keys(self):
        """Test handling of records missing label keys."""
        predictions = [
            {"id": 1, "true_label": "A", "predicted_label": "A"},
            {"id": 2, "true_label": "B"}, # missing predicted
            {"id": 3, "predicted_label": "C"}, # missing true
            {"id": 4, "true_label": "D", "predicted_label": "E"} # valid mismatch
        ]
        
        # This function currently logs a warning but continues. 
        # We expect it to skip invalid records and only return valid mismatches.
        misclassified = extract_misclassified(predictions)
        
        assert len(misclassified) == 1
        assert misclassified[0]['id'] == 4

    def test_save_misclassified_creates_file(self, tmp_path):
        """Test that save function creates the file and writes content."""
        misclassified = [
            {"id": 1, "true_label": "A", "predicted_label": "B"},
            {"id": 2, "true_label": "C", "predicted_label": "D"}
        ]
        output_file = tmp_path / "misclassified.jsonl"
        
        save_misclassified(misclassified, output_file)
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            lines = f.readlines()
        assert len(lines) == 2
        
        # Verify content structure
        parsed = [json.loads(line) for line in lines]
        assert parsed[0]['id'] == 1
        assert parsed[1]['id'] == 2

    def test_save_misclassified_creates_directories(self, tmp_path):
        """Test that save function creates parent directories if they don't exist."""
        misclassified = [{"id": 1}]
        nested_path = tmp_path / "deep" / "nested" / "dir" / "output.jsonl"
        
        save_misclassified(misclassified, nested_path)
        
        assert nested_path.exists()