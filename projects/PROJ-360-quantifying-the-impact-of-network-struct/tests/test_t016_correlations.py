import os
import json
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from analyze import compute_correlations, calculate_bonferroni_pvalues, load_metrics_csv

def test_compute_correlations_basic():
    """Test that correlations are computed correctly on known data."""
    # Create a mock DataFrame with perfect positive correlation
    data = {
        'material_id': ['m1', 'm2', 'm3', 'm4', 'm5'],
        'avg_degree': [1.0, 2.0, 3.0, 4.0, 5.0],
        'path_length': [5.0, 4.0, 3.0, 2.0, 1.0], # Perfect negative
        'clustering': [0.1, 0.2, 0.3, 0.4, 0.5],
        'thermal_conductivity_scalar': [10.0, 20.0, 30.0, 40.0, 50.0]
    }
    df = pd.DataFrame(data)
    
    results = compute_correlations(df)
    
    assert len(results) == 3, "Should compute 3 metrics"
    
    # Check avg_degree (perfect positive)
    deg_res = next(r for r in results if r['metric_name'] == 'avg_degree')
    assert abs(deg_res['pearson_coeff'] - 1.0) < 1e-5, "Pearson should be 1.0"
    assert deg_res['spearman_coeff'] == 1.0, "Spearman should be 1.0"
    
    # Check path_length (perfect negative)
    path_res = next(r for r in results if r['metric_name'] == 'path_length')
    assert abs(path_res['pearson_coeff'] - (-1.0)) < 1e-5, "Pearson should be -1.0"

def test_bonferroni_correction():
    """Test Bonferroni p-value adjustment."""
    results = [
        {'metric_name': 'm1', 'pearson_p_value': 0.01, 'spearman_p_value': 0.02},
        {'metric_name': 'm2', 'pearson_p_value': 0.04, 'spearman_p_value': 0.05},
        {'metric_name': 'm3', 'pearson_p_value': 0.10, 'spearman_p_value': 0.20}
    ]
    
    adjusted = calculate_bonferroni_pvalues(results)
    
    # 3 tests, so multiply by 3
    assert adjusted[0]['bonferroni_adjusted_pearson_p'] == 0.03
    assert adjusted[1]['bonferroni_adjusted_pearson_p'] == 0.12
    assert adjusted[2]['bonferroni_adjusted_pearson_p'] == 0.30
    
    # Significance check (alpha=0.05)
    assert adjusted[0]['is_significant'] == True  # 0.03 <= 0.05
    assert adjusted[1]['is_significant'] == False # 0.12 > 0.05
    assert adjusted[2]['is_significant'] == False

def test_load_metrics_csv_validation():
    """Test that load_metrics_csv fails on missing columns."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("material_id,avg_degree\nm1,1.0\n")
        temp_path = f.name
    
    try:
        load_metrics_csv(temp_path)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    finally:
        os.unlink(temp_path)
