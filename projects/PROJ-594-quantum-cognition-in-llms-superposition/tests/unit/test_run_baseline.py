import os
import sys
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock
import torch
import numpy as np

# Project root import adjustment
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from experiments.run_baseline import run_single_seed, main
from utils.config import set_environment

@patch('experiments.run_baseline.load_wic_dataset')
@patch('experiments.run_baseline.run_frozen_bert_inference')
@patch('experiments.run_baseline.compute_metrics')
def test_run_single_seed(mock_compute, mock_inference, mock_load):
    # Setup mocks
    mock_load.return_value = "mock_dataset"
    mock_inference.return_value = ([0, 1, 0, 1], [0, 1, 0, 1]) # Predictions, Labels
    mock_compute.return_value = {'accuracy': 0.95, 'macro_f1': 0.94}
    
    # Run
    result = run_single_seed(42)
    
    # Verify
    assert result['accuracy'] == 0.95
    assert result['macro_f1'] == 0.94
    mock_load.assert_called_once()
    mock_inference.assert_called_once()
    mock_compute.assert_called_once()

def test_main_output_generation():
    """Test that main() generates the expected JSON file with correct schema."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'baseline_metrics.json')
        
        # Mock dependencies to ensure deterministic output without real data
        with patch('experiments.run_baseline.load_wic_dataset'), \
             patch('experiments.run_baseline.run_frozen_bert_inference', return_value=([0]*10, [0]*10)), \
             patch('experiments.run_baseline.compute_metrics', return_value={'accuracy': 0.8, 'macro_f1': 0.75}):
            
            # Run main with specific args
            sys.argv = ['run_baseline.py', '--seeds', '42', '123', '--output-dir', tmpdir, '--variance-threshold', '0.1']
            try:
                main()
            except SystemExit:
                pass # Expected after completion
            
            # Verify file exists
            assert os.path.exists(output_path), "Output file was not created"
            
            # Verify schema
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert 'summary' in data
            assert 'accuracy' in data['summary']
            assert 'macro_f1' in data['summary']
            assert 'variance_accuracy' in data['summary']
            assert 'variance_macro_f1' in data['summary']
            assert 'per_seed_metrics' in data
            assert isinstance(data['summary']['accuracy'], float)
            assert isinstance(data['summary']['variance_accuracy'], float)