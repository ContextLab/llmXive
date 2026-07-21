import pytest
import csv
import os
import tempfile
from pathlib import Path
from data.sensitivity_analysis import calculate_sensitivity_metrics, append_sensitivity_to_log

def test_sensitivity_metrics_calculation():
    """
    Test that sensitivity metrics are calculated correctly.
    We create a small synthetic dataset with known manual labels and heuristic scores.
    """
    # Mock data
    data = [
        {'pr_number': 1, 'heuristic_score': 0.9, 'origin_label': 'Disclosing'}, # Should be Disclosing
        {'pr_number': 2, 'heuristic_score': 0.2, 'origin_label': 'Non-Disclosing'}, # Should be Non-Disclosing
        {'pr_number': 3, 'heuristic_score': 0.8, 'origin_label': 'Disclosing'}, # Should be Disclosing
        {'pr_number': 4, 'heuristic_score': 0.3, 'origin_label': 'Non-Disclosing'}, # Should be Non-Disclosing
        {'pr_number': 5, 'heuristic_score': 0.5, 'origin_label': 'Non-Disclosing'}, # Should be Non-Disclosing
    ]
    
    # Manual ground truth: 1, 3 are Disclosing; 2, 4, 5 are Non-Disclosing
    manual_labels = {
        1: 'Disclosing',
        2: 'Non-Disclosing',
        3: 'Disclosing',
        4: 'Non-Disclosing',
        5: 'Non-Disclosing'
    }
    
    # Test with threshold 0.5
    # Predictions:
    # 1 (0.9 >= 0.5) -> Disclosing (TP)
    # 2 (0.2 < 0.5) -> Non-Disclosing (TN)
    # 3 (0.8 >= 0.5) -> Disclosing (TP)
    # 4 (0.3 < 0.5) -> Non-Disclosing (TN)
    # 5 (0.5 >= 0.5) -> Disclosing (FP) -> Error!
    
    thresholds = [0.5]
    results = calculate_sensitivity_metrics(data, thresholds, manual_labels)
    
    assert len(results) == 1
    res = results[0]
    
    assert res['threshold'] == 0.5
    assert res['tp'] == 2
    assert res['tn'] == 2
    assert res['fp'] == 1 # PR 5
    assert res['fn'] == 0
    
    # Accuracy = (2+2)/5 = 0.8
    assert abs(res['accuracy'] - 0.8) < 1e-6
    
    # FPR = FP / (FP + TN) = 1 / (1 + 2) = 1/3
    assert abs(res['false_positive_rate'] - (1/3)) < 1e-6
    
    # FNR = FN / (FN + TP) = 0 / 2 = 0
    assert res['false_negative_rate'] == 0.0

def test_append_sensitivity_to_log():
    """Test that results are correctly appended to a CSV log file."""
    results = [
        {'threshold': 0.5, 'accuracy': 0.8, 'false_positive_rate': 0.33, 'false_negative_rate': 0.0, 'tp': 2, 'tn': 2, 'fp': 1, 'fn': 0}
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
        tmp_path = tmp.name
    
    try:
        append_sensitivity_to_log(results, tmp_path)
        
        with open(tmp_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 1
        assert rows[0]['threshold'] == '0.5'
        assert rows[0]['accuracy'] == '0.8'
        assert rows[0]['analysis_type'] == 'sensitivity_sweep'
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
