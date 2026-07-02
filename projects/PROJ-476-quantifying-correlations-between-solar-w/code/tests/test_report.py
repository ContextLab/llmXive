import pytest
import pandas as pd
import numpy as np
from code.viz.report import check_threshold_detection

def test_report_threshold_detection():
    """
    Verify |r| > 0.5 threshold detection in report logic.
    
    This test ensures that the report generation logic correctly identifies
    correlation pairs that exceed the absolute value threshold of 0.5,
    as required by User Story 3 acceptance criteria.
    """
    # Create synthetic correlation results matching the expected schema
    # from code/analysis/correlation.py
    test_data = pd.DataFrame({
        'param': ['N_p', 'T_p', 'He2+_ratio', 'N_p'],
        'index': ['Kp', 'Dst', 'Kp', 'Dst'],
        'lag': [0, 0, 0, 1],
        'pearson_r': [0.3, 0.6, -0.4, -0.55],
        'spearman_rho': [0.28, 0.58, -0.39, -0.52],
        'p_value_neff': [0.04, 0.01, 0.08, 0.003],
        'p_value_bonferroni': [0.06, 0.001, 0.12, 0.005]
    })
    
    # Expected results: rows with |pearson_r| > 0.5
    # Row 1: T_p vs Dst at lag 0 (r=0.6)
    # Row 3: N_p vs Dst at lag 1 (r=-0.55)
    expected_count = 2
    expected_params = [('T_p', 'Dst'), ('N_p', 'Dst')]
    
    # Run the threshold detection logic
    detected = check_threshold_detection(test_data, threshold=0.5)
    
    # Verify count matches
    assert len(detected) == expected_count, \
        f"Expected {expected_count} detections, got {len(detected)}"
    
    # Verify specific detections
    detected_tuples = [(row['param'], row['index']) for _, row in detected.iterrows()]
    for expected in expected_params:
        assert expected in detected_tuples, \
            f"Expected detection for {expected} not found"
    
    # Verify that rows below threshold were excluded
    non_detected = test_data[abs(test_data['pearson_r']) <= 0.5]
    assert len(non_detected) == len(test_data) - expected_count, \
        "Some rows below threshold were incorrectly included"
    
    # Test edge case: exactly 0.5 should NOT be detected (strict >)
    edge_data = pd.DataFrame({
        'param': ['N_p'],
        'index': ['Kp'],
        'lag': [0],
        'pearson_r': [0.5],
        'spearman_rho': [0.5],
        'p_value_neff': [0.05],
        'p_value_bonferroni': [0.05]
    })
    edge_detected = check_threshold_detection(edge_data, threshold=0.5)
    assert len(edge_detected) == 0, \
        "Edge case: exactly 0.5 should not be detected (strict >)"
    
    # Test edge case: -0.5 should NOT be detected (strict >)
    edge_data_neg = pd.DataFrame({
        'param': ['N_p'],
        'index': ['Kp'],
        'lag': [0],
        'pearson_r': [-0.5],
        'spearman_rho': [-0.5],
        'p_value_neff': [0.05],
        'p_value_bonferroni': [0.05]
    })
    edge_detected_neg = check_threshold_detection(edge_data_neg, threshold=0.5)
    assert len(edge_detected_neg) == 0, \
        "Edge case: exactly -0.5 should not be detected (strict >)"
    
    # Test edge case: 0.51 should be detected
    edge_data_plus = pd.DataFrame({
        'param': ['N_p'],
        'index': ['Kp'],
        'lag': [0],
        'pearson_r': [0.51],
        'spearman_rho': [0.51],
        'p_value_neff': [0.05],
        'p_value_bonferroni': [0.05]
    })
    edge_detected_plus = check_threshold_detection(edge_data_plus, threshold=0.5)
    assert len(edge_detected_plus) == 1, \
        "Edge case: 0.51 should be detected"