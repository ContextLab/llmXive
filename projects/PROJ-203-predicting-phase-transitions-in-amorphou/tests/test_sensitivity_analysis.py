"""
Tests for Sensitivity Analysis (T019).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import numpy as np

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.sensitivity_analysis import calculate_metrics, main

def test_calculate_metrics_basic():
    """Test basic metric calculation."""
    # Create a mock dataframe
    data = {
        'Tg_exp': [500.0, 500.0, 500.0, 500.0],
        'Tx_exp': [540.0, 560.0, 520.0, 510.0], # Diffs: 40, 60, 20, 10
        'crystallization_label': [1, 0, 1, 1]   # Baseline (50K) labels: 1 if diff<=50
    }
    # Diffs: 40 (<=50 -> 1), 60 (>50 -> 0), 20 (<=50 -> 1), 10 (<=50 -> 1)
    # Existing labels match the diffs for 50K.
    
    df = pd.DataFrame(data)
    
    # Test with threshold 30K
    # New Labels (<=30): 40->0, 60->0, 20->1, 10->1 => [0, 0, 1, 1]
    # Predictions (Baseline 50K): [1, 0, 1, 1]
    # Comparison:
    # Row 0: True=0, Pred=1 -> FP
    # Row 1: True=0, Pred=0 -> TN
    # Row 2: True=1, Pred=1 -> TP
    # Row 3: True=1, Pred=1 -> TP
    
    # Accuracy: 3/4 = 0.75
    # Class Balance: 2/4 = 0.5
    # FPR: FP / (FP + TN) = 1 / (1 + 1) = 0.5
    
    metrics = calculate_metrics(df, 30.0)
    
    assert metrics['threshold_K'] == 30.0
    assert metrics['class_balance'] == 0.5
    assert metrics['accuracy_vs_baseline_50K'] == 0.75
    assert metrics['fpr_vs_baseline_50K'] == 0.5
    assert metrics['num_positives'] == 2
    assert metrics['num_negatives'] == 2

def test_calculate_metrics_edge_case_all_positive():
    """Test when all samples are positive at a high threshold."""
    data = {
        'Tg_exp': [500.0, 500.0],
        'Tx_exp': [510.0, 520.0], # Diffs: 10, 20
        'crystallization_label': [1, 1]
    }
    df = pd.DataFrame(data)
    
    # Threshold 100K -> All True
    metrics = calculate_metrics(df, 100.0)
    
    assert metrics['class_balance'] == 1.0
    # If all are True, and predictions are all True, Accuracy = 1.0
    assert metrics['accuracy_vs_baseline_50K'] == 1.0
    # FPR = FP / (FP+TN). If all True, TN=0, FP=0. FPR = 0/0 -> 0.0 (handled in code)
    assert metrics['fpr_vs_baseline_50K'] == 0.0

def test_main_integration(tmp_path):
    """Test the main function with a temporary dataset."""
    # Create a temporary dataset
    data = {
        'Tg_exp': [500.0] * 10,
        'Tx_exp': [510.0, 520.0, 530.0, 540.0, 550.0, 560.0, 570.0, 580.0, 590.0, 600.0],
        'crystallization_label': [1, 1, 1, 1, 1, 0, 0, 0, 0, 0] # 50K threshold split
    }
    df = pd.DataFrame(data)
    
    input_file = tmp_path / "final_dataset.parquet"
    df.to_parquet(input_file)
    
    output_file = tmp_path / "sensitivity_report.json"
    
    # Mock config to use our temp paths
    with patch('models.sensitivity_analysis.get_config') as mock_config:
        mock_config.return_value = None # Not used directly in main if we patch paths
        with patch('models.sensitivity_analysis.get_paths') as mock_paths:
            mock_paths.return_value = {
                'processed_dataset': str(input_file),
                'sensitivity_report': str(output_file)
            }
            
            # Run main
            main()
            
            # Verify output exists
            assert output_file.exists()
            
            # Verify content
            with open(output_file, 'r') as f:
                report = json.load(f)
            
            assert len(report) == 16 # 25 to 100 in steps of 5
            assert report[0]['threshold_K'] == 25
            assert report[-1]['threshold_K'] == 100

if __name__ == "__main__":
    test_calculate_metrics_basic()
    test_calculate_metrics_edge_case_all_positive()
    test_main_integration(tempfile.mkdtemp())
    print("All tests passed.")
