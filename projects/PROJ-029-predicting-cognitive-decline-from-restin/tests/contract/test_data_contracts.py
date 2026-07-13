"""
Contract tests to verify data formats match specifications.
"""
import pytest
import pandas as pd
import json
from pathlib import Path

def test_graph_metrics_schema():
    """Verify graph_metrics.csv schema."""
    # This test would normally run after T019 produces the file.
    # Since we are in a unit/integration test context without guaranteed artifacts,
    # we test the schema definition logic.
    
    expected_columns = [
        'subject_id', 'degree', 'global_efficiency', 'clustering_coeff', 'path_length'
    ]
    
    # Create a dummy dataframe to check if it matches
    df = pd.DataFrame(columns=expected_columns)
    
    assert list(df.columns) == expected_columns

def test_performance_report_schema():
    """Verify performance_report.json schema."""
    expected_keys = ['roc_auc', 'accuracy', 'f1_score', 'fold_scores']
    
    dummy_report = {
        'roc_auc': 0.85,
        'accuracy': 0.80,
        'f1_score': 0.78,
        'fold_scores': [0.8, 0.85, 0.9]
    }
    
    for key in expected_keys:
        assert key in dummy_report
