import os
import json
import tempfile
import pytest
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor

# Import the function to test
from analysis.reporting import generate_confounder_report, detect_proxy_variables

def test_detect_proxy_variables_found():
    """Test detection when proxy variables are present."""
    df = pd.DataFrame({
        'rolling_temperature': [1, 2, 3],
        'grain_size': [10, 20, 30],
        'strain_rate': [0.1, 0.2, 0.3],
        'cooling_rate': [5, 6, 7],
        'Mg': [0.5, 0.6, 0.7]
    })
    
    proxies = detect_proxy_variables(df)
    assert 'strain_rate' in proxies
    assert 'cooling_rate' in proxies
    assert len(proxies) == 2

def test_detect_proxy_variables_not_found():
    """Test detection when proxy variables are absent."""
    df = pd.DataFrame({
        'rolling_temperature': [1, 2, 3],
        'grain_size': [10, 20, 30],
        'Mg': [0.5, 0.6, 0.7]
    })
    
    proxies = detect_proxy_variables(df)
    assert len(proxies) == 0

def test_generate_confounder_report_no_proxies(tmp_path):
    """Test report generation when no proxies are found."""
    # Mock config paths
    import analysis.reporting as reporting_module
    original_get_config = reporting_module.get_config
    
    def mock_config():
        return {
            'paths': {
                'artifacts': str(tmp_path)
            }
        }
    
    reporting_module.get_config = mock_config
    
    try:
        df = pd.DataFrame({
            'rolling_temperature': [1, 2, 3],
            'grain_size': [10, 20, 30],
            'Mg': [0.5, 0.6, 0.7]
        })
        
        # Create a dummy model
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        model.fit(df[['rolling_temperature', 'Mg']], df['grain_size'])
        
        report = generate_confounder_report(df, model)
        
        assert report['status'] == 'N/A'
        assert report['proxy_variables'] == []
        assert report['r2_delta'] is None
        
        # Verify file exists
        output_file = os.path.join(tmp_path, 'confounder_report.json')
        assert os.path.exists(output_file)
        
        with open(output_file, 'r') as f:
            saved_report = json.load(f)
        
        assert saved_report['status'] == 'N/A'
    finally:
        reporting_module.get_config = original_get_config

def test_generate_confounder_report_with_proxies(tmp_path):
    """Test report generation when proxies are found and refit occurs."""
    import analysis.reporting as reporting_module
    original_get_config = reporting_module.get_config
    
    def mock_config():
        return {
            'paths': {
                'artifacts': str(tmp_path)
            }
        }
    
    reporting_module.get_config = mock_config
    
    try:
        # Create dataset with proxies and enough rows for refit
        n = 100
        df = pd.DataFrame({
            'rolling_temperature': np.random.rand(n) * 100,
            'grain_size': np.random.rand(n) * 100,
            'strain_rate': np.random.rand(n),
            'Mg': np.random.rand(n),
            'Si': np.random.rand(n)
        })
        
        # Create a dummy model
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        model.fit(df[['rolling_temperature', 'Mg', 'Si']], df['grain_size'])
        
        report = generate_confounder_report(df, model)
        
        assert report['status'] == 'computed'
        assert 'strain_rate' in report['proxy_variables']
        assert report['r2_delta'] is not None
        assert isinstance(report['r2_delta'], float)
        
        # Verify file exists and schema
        output_file = os.path.join(tmp_path, 'confounder_report.json')
        assert os.path.exists(output_file)
        
        with open(output_file, 'r') as f:
            saved_report = json.load(f)
        
        assert saved_report['status'] == 'computed'
        assert 'r2_delta' in saved_report
    finally:
        reporting_module.get_config = original_get_config