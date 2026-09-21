"""Unit tests for T024: Collinearity diagnostics (VIF)."""
import os
import sys
import json
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.collinearity import (
    calculate_vif, 
    run_collinearity_diagnostics, 
    save_collinearity_report,
    VIF_THRESHOLD
)

@pytest.fixture
def sample_data():
    """Create sample data for VIF testing."""
    np.random.seed(42)
    n = 50
    data = {
        'participant_id': range(n),
        'Fatigue_Delta': np.random.randn(n) * 10,
        'Pre_Complexity': np.random.randn(n) * 5,
        'age': np.random.randint(20, 60, n),
        'time_of_day': np.random.choice([0, 1], n),  # 0=Morning, 1=Afternoon
        'medication_status': np.random.choice([0, 1], n)  # 0=No, 1=Yes
    }
    # Add some correlation to test VIF
    data['Pre_Complexity'] = data['Fatigue_Delta'] * 0.3 + np.random.randn(n) * 2
    return pd.DataFrame(data)

@pytest.fixture
def high_collinearity_data():
    """Create data with high collinearity to test VIF threshold."""
    np.random.seed(42)
    n = 50
    base = np.random.randn(n) * 10
    data = {
        'participant_id': range(n),
        'Fatigue_Delta': base,
        'Pre_Complexity': base * 0.95 + np.random.randn(n) * 0.5,  # High correlation
        'age': np.random.randint(20, 60, n)
    }
    return pd.DataFrame(data)

def test_calculate_vif_basic(sample_data):
    """Test basic VIF calculation."""
    predictors = ['Fatigue_Delta', 'Pre_Complexity', 'age']
    vif_results = calculate_vif(sample_data, predictors)
    
    assert len(vif_results) == len(predictors)
    for pred, vif_val in vif_results.items():
        assert isinstance(vif_val, float)
        assert vif_val >= 1.0  # VIF is always >= 1

def test_calculate_vif_high_collinearity(high_collinearity_data):
    """Test VIF calculation with high collinearity."""
    predictors = ['Fatigue_Delta', 'Pre_Complexity']
    vif_results = calculate_vif(high_collinearity_data, predictors)
    
    # With high correlation, VIF should be high (> 5)
    assert vif_results['Fatigue_Delta'] > VIF_THRESHOLD or vif_results['Pre_Complexity'] > VIF_THRESHOLD

def test_run_collinearity_diagnostics(sample_data):
    """Test full diagnostics run."""
    import logging
    logger = logging.getLogger("test_collinearity")
    
    valid_predictors, vif_results = run_collinearity_diagnostics(sample_data, logger)
    
    assert isinstance(valid_predictors, list)
    assert isinstance(vif_results, dict)
    assert len(vif_results) >= 2  # At least Fatigue_Delta and Pre_Complexity
    assert all(pred in vif_results for pred in valid_predictors)

def test_run_collinearity_diagnostics_high_collinearity(high_collinearity_data):
    """Test diagnostics with high collinearity - should exclude collinear predictors."""
    import logging
    logger = logging.getLogger("test_collinearity_high")
    
    valid_predictors, vif_results = run_collinearity_diagnostics(high_collinearity_data, logger)
    
    # At least one predictor should be excluded due to high VIF
    assert len(valid_predictors) < len(high_collinearity_data.columns) - 1

def test_save_collinearity_report(sample_data, tmp_path):
    """Test saving VIF report."""
    import logging
    logger = logging.getLogger("test_collinearity_save")
    
    # Temporarily override paths for testing
    import code.collinearity as coll_module
    original_log_path = coll_module.DIAGNOSTICS_LOG_PATH
    original_json_path = coll_module.VALID_PREDICTORS_JSON_PATH
    
    coll_module.DIAGNOSTICS_LOG_PATH = str(tmp_path / "vif_diagnostics.log")
    coll_module.VALID_PREDICTORS_JSON_PATH = str(tmp_path / "vif_valid_predictors.json")
    
    try:
        valid_predictors, vif_results = run_collinearity_diagnostics(sample_data, logger)
        save_collinearity_report(valid_predictors, vif_results, logger)
        
        # Check log file
        assert os.path.exists(coll_module.DIAGNOSTICS_LOG_PATH)
        with open(coll_module.DIAGNOSTICS_LOG_PATH, 'r') as f:
            log_content = f.read()
        assert "VIF Diagnostics" in log_content
        assert "Fatigue_Delta" in log_content
        assert "Pre_Complexity" in log_content
        
        # Check JSON file
        assert os.path.exists(coll_module.VALID_PREDICTORS_JSON_PATH)
        with open(coll_module.VALID_PREDICTORS_JSON_PATH, 'r') as f:
            json_data = json.load(f)
        assert "valid_predictors" in json_data
        assert "vif_threshold" in json_data
        assert "all_vif_values" in json_data
        assert json_data["vif_threshold"] == VIF_THRESHOLD
    finally:
        # Restore original paths
        coll_module.DIAGNOSTICS_LOG_PATH = original_log_path
        coll_module.VALID_PREDICTORS_JSON_PATH = original_json_path

def test_vif_threshold_logic(sample_data):
    """Test that VIF threshold logic correctly identifies valid predictors."""
    import logging
    logger = logging.getLogger("test_threshold")
    
    # Create data where one predictor is clearly collinear
    np.random.seed(42)
    n = 50
    base = np.random.randn(n) * 10
    data = {
        'Fatigue_Delta': base,
        'Pre_Complexity': base * 0.99 + np.random.randn(n) * 0.1,  # Very high correlation
        'age': np.random.randint(20, 60, n)
    }
    df = pd.DataFrame(data)
    
    valid_predictors, vif_results = run_collinearity_diagnostics(df, logger)
    
    # One of the highly correlated predictors should be excluded
    assert len(valid_predictors) < 3  # Not all predictors are valid

def test_empty_predictors():
    """Test behavior with insufficient predictors."""
    import logging
    logger = logging.getLogger("test_empty")
    
    df = pd.DataFrame({'Fatigue_Delta': [1, 2, 3]})
    valid_predictors, vif_results = run_collinearity_diagnostics(df, logger)
    
    # With only one predictor, VIF is not meaningful, but it should not crash
    assert len(valid_predictors) == 1
    assert valid_predictors[0] == 'Fatigue_Delta'