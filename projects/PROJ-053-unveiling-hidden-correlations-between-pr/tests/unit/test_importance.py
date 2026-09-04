import pytest
import json
import os
import tempfile
from pathlib import Path
import numpy as np

# Mock config for testing if necessary, but we assume config is available
# We test the logic of T031

def test_load_literature_baseline_missing_citation(monkeypatch):
    """Test that ValueError is raised if no baseline is found."""
    from utils.importance_analyzer import load_literature_baseline
    
    # Mock get_hardcoded_baseline_ranking and get_literature_citation to return None
    import utils.importance_analyzer as imp_mod
    import config as cfg_mod
    
    original_hardcoded = cfg_mod.get_hardcoded_baseline_ranking
    original_citation = cfg_mod.get_literature_citation
    
    cfg_mod.get_hardcoded_baseline_ranking = lambda: None
    cfg_mod.get_literature_citation = lambda: None
    
    with pytest.raises(ValueError) as excinfo:
        load_literature_baseline("test_key")
    
    assert "Verified Accuracy Violation" in str(excinfo.value)
    
    # Restore
    cfg_mod.get_hardcoded_baseline_ranking = original_hardcoded
    cfg_mod.get_literature_citation = original_citation

def test_run_correlation_analysis_with_mock_data(monkeypatch):
    """Test the full correlation analysis flow with mock data."""
    from utils.importance_analyzer import run_correlation_analysis
    import pickle
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import RBF
    
    # Create temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # 1. Create Mock Model
        model = GaussianProcessRegressor(kernel=RBF(length_scale=1.0))
        # Dummy fit to make it callable (though we mock predict)
        X_dummy = np.random.rand(10, 3)
        y_dummy = np.random.rand(10)
        model.fit(X_dummy, y_dummy)
        
        model_path = tmpdir / "model.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        # 2. Create Mock Test Data
        test_data = {
            'laser_power': [100.0, 200.0, 300.0, 400.0, 500.0],
            'scan_speed': [500.0, 400.0, 300.0, 200.0, 100.0],
            'layer_thickness': [0.03, 0.03, 0.03, 0.03, 0.03],
            'yield_strength': [300.0, 350.0, 400.0, 450.0, 500.0]
        }
        import pandas as pd
        df = pd.DataFrame(test_data)
        test_path = tmpdir / "test.csv"
        df.to_csv(test_path, index=False)
        
        # 3. Create Mock Metrics
        metrics_path = tmpdir / "metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump({"existing_metric": 1.0}, f)
        
        # 4. Run Analysis
        # We need to mock the config paths or pass absolute paths
        # The function expects paths, so we pass absolute paths here.
        result = run_correlation_analysis(
            model_path=str(model_path),
            test_data_path=str(test_path),
            output_path=str(metrics_path),
            user_baseline_path=None # Force literature load
        )
        
        assert 'permutation_importance_correlation' in result
        assert 'baseline_source' in result
        assert result['baseline_source'] == 'literature_citation'
        # Correlation should be a float
        assert isinstance(result['permutation_importance_correlation'], float)

def test_calculate_correlation_coefficient():
    """Test the Spearman correlation calculation."""
    from utils.importance_analyzer import calculate_correlation_coefficient
    
    list1 = [1.0, 2.0, 3.0, 4.0, 5.0]
    list2 = [1.0, 2.0, 3.0, 4.0, 5.0]
    
    corr = calculate_correlation_coefficient(list1, list2)
    assert abs(corr - 1.0) < 0.001
    
    list2_inv = [5.0, 4.0, 3.0, 2.0, 1.0]
    corr_inv = calculate_correlation_coefficient(list1, list2_inv)
    assert abs(corr_inv - (-1.0)) < 0.001
