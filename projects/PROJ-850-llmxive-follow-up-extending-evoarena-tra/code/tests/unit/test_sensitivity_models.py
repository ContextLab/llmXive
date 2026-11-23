import pytest
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.heuristics.sensitivity_models import (
    calculate_metrics,
    get_model_param_count,
    format_params,
    run_sensitivity_analysis,
    write_results_to_csv
)

@pytest.fixture
def synthetic_data():
    """Create synthetic data for testing."""
    return [
        {'patch_a': 'The sky is blue.', 'patch_b': 'The sky is blue.', 'is_contradiction': False},
        {'patch_a': 'The sky is blue.', 'patch_b': 'The sky is green.', 'is_contradiction': True},
        {'patch_a': 'The cat is sleeping.', 'patch_b': 'The cat is sleeping.', 'is_contradiction': False},
        {'patch_a': 'The cat is sleeping.', 'patch_b': 'The cat is running.', 'is_contradiction': True},
    ]

@pytest.fixture
def output_dir(tmp_path):
    """Create a temporary directory for output files."""
    return tmp_path / 'output'

class TestCalculateMetrics:
    def test_perfect_accuracy(self):
        predictions = [True, False, True, False]
        labels = [True, False, True, False]
        metrics = calculate_metrics(predictions, labels)
        assert metrics['accuracy'] == 1.0
        assert metrics['precision'] == 1.0
        assert metrics['recall'] == 1.0
        assert metrics['f1'] == 1.0

    def test_no_true_positives(self):
        predictions = [False, False, False, False]
        labels = [True, True, True, True]
        metrics = calculate_metrics(predictions, labels)
        assert metrics['accuracy'] == 0.0
        assert metrics['precision'] == 0.0
        assert metrics['recall'] == 0.0
        assert metrics['f1'] == 0.0

    def test_empty_lists(self):
        metrics = calculate_metrics([], [])
        assert metrics['accuracy'] == 0.0
        assert metrics['precision'] == 0.0
        assert metrics['recall'] == 0.0
        assert metrics['f1'] == 0.0

class TestFormatParams:
    def test_millions(self):
        assert format_params(110000000) == '110M'

    def test_thousands(self):
        assert format_params(15000) == '15K'

    def test_small(self):
        assert format_params(500) == '500'

@patch('src.heuristics.sensitivity_models.AutoModelForSequenceClassification')
@patch('src.heuristics.sensitivity_models.AutoTokenizer')
@patch('src.heuristics.sensitivity_models.ConflictDetector')
def test_run_sensitivity_analysis_structure(self, mock_detector_class, mock_tokenizer, mock_model, synthetic_data):
    """Test that run_sensitivity_analysis returns the expected structure."""
    # Mock the model parameter count
    mock_model_instance = MagicMock()
    mock_model_instance.num_parameters.return_value = 110000000
    mock_model.from_pretrained.return_value = mock_model_instance

    # Mock the detector
    mock_detector = MagicMock()
    mock_detector.predict.return_value = [True, False, True, False]
    mock_detector_class.return_value = mock_detector

    result = run_sensitivity_analysis('test-model', 0.5, synthetic_data)

    assert 'model_name' in result
    assert 'params' in result
    assert 'accuracy' in result
    assert 'latency' in result
    assert 'threshold_used' in result
    assert result['model_name'] == 'test-model'
    assert result['threshold_used'] == 0.5
    assert isinstance(result['accuracy'], float)
    assert isinstance(result['latency'], float)

def test_write_results_to_csv(output_dir):
    """Test that write_results_to_csv creates a valid CSV file."""
    results = [
        {'model_name': 'model1', 'params': '110M', 'accuracy': 0.9, 'latency': 0.1, 'threshold_used': 0.5},
        {'model_name': 'model2', 'params': '88M', 'accuracy': 0.85, 'latency': 0.15, 'threshold_used': 0.7},
    ]
    output_path = output_dir / 'test.csv'

    write_results_to_csv(results, output_path)

    assert output_path.exists()
    with open(output_path, 'r') as f:
        lines = f.readlines()
        assert len(lines) == 3  # Header + 2 data rows
        assert 'model_name' in lines[0]
        assert 'accuracy' in lines[0]
        assert 'model1' in lines[1]
        assert 'model2' in lines[2]