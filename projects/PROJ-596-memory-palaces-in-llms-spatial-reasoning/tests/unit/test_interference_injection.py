import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
from scipy import stats

# Import the function to test
from evaluation.metrics import compute_interference_distance, compute_exact_match_recall

class TestInterferenceInjection:
    @pytest.fixture
    def mock_dataset(self):
        """Create a mock dataset for testing."""
        return [
            {"input": "The cat is on the mat.", "target": "on the mat"},
            {"input": "The dog is in the house.", "target": "in the house"},
            {"input": "The bird is in the sky.", "target": "in the sky"},
        ]
    
    @pytest.fixture
    def mock_model_spatial(self):
        """Mock spatial model."""
        model = MagicMock()
        model.generate = MagicMock(return_value=MagicMock(__iter__=lambda self: iter([b"The cat is on the mat"])))
        return model
    
    @pytest.fixture
    def mock_model_baseline(self):
        """Mock baseline model."""
        model = MagicMock()
        model.generate = MagicMock(return_value=MagicMock(__iter__=lambda self: iter([b"The cat is on the mat"])))
        return model
    
    @pytest.fixture
    def mock_tokenizer(self):
        """Mock tokenizer."""
        tokenizer = MagicMock()
        tokenizer.__call__ = MagicMock(return_value={"input_ids": [[1, 2, 3]]})
        tokenizer.decode = MagicMock(return_value="The cat is on the mat")
        tokenizer.max_length = 512
        return tokenizer

    def test_compute_exact_match_recall(self):
        """Test exact match recall calculation."""
        predictions = ["A", "B", "C"]
        references = ["A", "B", "D"]
        recall = compute_exact_match_recall(predictions, references)
        assert recall == 2/3

    @patch('evaluation.metrics.load_dataset')
    @patch('evaluation.metrics.load_model')
    @patch('evaluation.metrics.AutoTokenizer')
    def test_compute_interference_distance_structure(self, mock_tokenizer_class, mock_load_model, mock_load_dataset, mock_dataset):
        """Test the structure of the interference distance computation."""
        # Setup mocks
        mock_load_dataset.return_value = mock_dataset
        mock_load_model.side_effect = [
            (MagicMock(), MagicMock()), # Spatial model
            (MagicMock(), MagicMock())  # Baseline model
        ]
        mock_tokenizer_class.from_pretrained.return_value = MagicMock(decode=lambda x, **kwargs: "mocked text")
        
        # Call the function
        result = compute_interference_distance(
            dataset_name="babi",
            spatial_variant="spatial",
            baseline_variant="baseline"
        )
        
        # Assert result structure
        assert "spatial_recall" in result
        assert "baseline_recall" in result
        assert "delta" in result
        assert "p_value" in result
        assert isinstance(result["spatial_recall"], float)
        assert isinstance(result["baseline_recall"], float)
        assert isinstance(result["delta"], float)
        assert isinstance(result["p_value"], float)

    def test_interference_metrics_json_output(self, tmp_path):
        """Test that interference metrics are saved to JSON."""
        # This test is more of an integration test, but we can test the saving logic
        data = {
            "dataset": "babi",
            "spatial_recall": 0.8,
            "baseline_recall": 0.6,
            "delta": 0.2,
            "p_value": 0.05
        }
        
        output_path = tmp_path / "interference_metrics.json"
        with open(output_path, 'w') as f:
            json.dump(data, f)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            loaded_data = json.load(f)
        assert loaded_data == data
