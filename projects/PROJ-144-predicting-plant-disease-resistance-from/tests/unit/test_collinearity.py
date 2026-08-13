import os
import json
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(project_root))

from modeling.collinearity import calculate_vif, flag_high_collinearity, run_collinearity_diagnostics

def test_calculate_vif_basic():
    """Test VIF calculation with simple known data."""
    # Create a simple dataset with known collinearity
    np.random.seed(42)
    n = 100
    X = pd.DataFrame({
        'feature1': np.random.normal(0, 1, n),
        'feature2': np.random.normal(0, 1, n),
        'feature3': np.random.normal(0, 1, n)
    })
    
    # Add a highly correlated feature
    X['feature4'] = X['feature1'] * 2 + np.random.normal(0, 0.1, n)
    
    vif_values = calculate_vif(X, ['feature1', 'feature2', 'feature3', 'feature4'])
    
    assert len(vif_values) == 4
    # feature4 should have high VIF due to correlation with feature1
    assert vif_values[3] > 5.0, "feature4 should have high VIF"
    
def test_flag_high_collinearity():
    """Test flagging of high collinearity features."""
    vif_scores = [
        {"feature_name": "f1", "vif_value": 1.5},
        {"feature_name": "f2", "vif_value": 6.2},
        {"feature_name": "f3", "vif_value": 3.1},
        {"feature_name": "f4", "vif_value": 10.5}
    ]
    
    flagged = flag_high_collinearity(vif_scores, threshold=5.0)
    
    assert len(flagged) == 2
    assert flagged[0]['feature_name'] == 'f2'
    assert flagged[1]['feature_name'] == 'f4'
    
def test_run_collinearity_diagnostics(tmp_path):
    """Test full collinearity diagnostics pipeline."""
    # Create temporary input file
    input_path = tmp_path / "test_matrix.csv"
    output_path = tmp_path / "vif_results.json"
    
    # Generate test data
    np.random.seed(42)
    n = 50
    df = pd.DataFrame({
        'metabolite_1': np.random.normal(0, 1, n),
        'metabolite_2': np.random.normal(0, 1, n),
        'metabolite_3': np.random.normal(0, 1, n),
        'metabolite_4': np.random.normal(0, 1, n)
    })
    # Add collinear feature
    df['metabolite_5'] = df['metabolite_1'] * 2 + np.random.normal(0, 0.1, n)
    
    df.to_csv(input_path, index=False)
    
    # Run diagnostics
    results = run_collinearity_diagnostics(
        feature_matrix_path=str(input_path),
        output_path=str(output_path),
        threshold=5.0
    )
    
    # Verify output file exists
    assert output_path.exists()
    assert output_path.stat().st_size > 0
    
    # Verify results structure
    assert 'vif_scores' in results
    assert 'high_collinearity_features' in results
    assert 'threshold_used' in results
    assert results['threshold_used'] == 5.0
    
    # Verify at least one feature is flagged
    assert len(results['high_collinearity_features']) >= 1
    
    # Verify JSON content matches results
    with open(output_path, 'r') as f:
        saved_data = json.load(f)
        
    assert saved_data['vif_scores'] == results['vif_scores']
    assert saved_data['high_collinearity_features'] == results['high_collinearity_features']
    
def test_empty_dataframe():
    """Test VIF calculation with empty dataframe."""
    X = pd.DataFrame()
    vif_values = calculate_vif(X, [])
    assert vif_values == []
    
def test_nonexistent_file():
    """Test diagnostics with non-existent file."""
    with pytest.raises(FileNotFoundError):
        run_collinearity_diagnostics(
            feature_matrix_path="/nonexistent/path.csv",
            output_path="/tmp/output.json"
        )
