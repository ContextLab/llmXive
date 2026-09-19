import json
import pytest
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.reporting import generate_confounder_report, detect_proxy_variables

@pytest.fixture
def mock_df_with_proxies():
    """Create a mock dataframe with known proxy variables."""
    data = {
        'rolling_temp': np.random.rand(100) * 100,
        'Mg': np.random.rand(100),
        'Si': np.random.rand(100),
        'grain_size': np.random.rand(100) * 10,
        'strain_rate': np.random.rand(100),  # Proxy
        'cooling_rate': np.random.rand(100), # Proxy
        'other_feature': np.random.rand(100)
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_df_without_proxies():
    """Create a mock dataframe without proxy variables."""
    data = {
        'rolling_temp': np.random.rand(100) * 100,
        'Mg': np.random.rand(100),
        'Si': np.random.rand(100),
        'grain_size': np.random.rand(100) * 10,
        'other_feature': np.random.rand(100)
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_model():
    """Create a dummy fitted model."""
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    # Fit on dummy data to ensure it has feature_names_in_
    X_dummy = np.random.rand(20, 3)
    y_dummy = np.random.rand(20)
    model.fit(X_dummy, y_dummy)
    return model

def test_detect_proxy_variables_present(mock_df_with_proxies):
    """Test detection of proxy variables when they exist."""
    proxies = detect_proxy_variables(mock_df_with_proxies)
    assert 'strain_rate' in proxies
    assert 'cooling_rate' in proxies
    assert len(proxies) >= 2

def test_detect_proxy_variables_absent(mock_df_without_proxies):
    """Test detection returns empty list when proxies are absent."""
    proxies = detect_proxy_variables(mock_df_without_proxies)
    assert len(proxies) == 0

def test_generate_confounder_report_with_proxies(mock_df_with_proxies, mock_model, tmp_path, monkeypatch):
    """Test report generation when proxies exist."""
    # Mock get_config to use tmp_path for artifacts
    import analysis.reporting as reporting_module
    original_get_config = reporting_module.get_config
    
    def mock_get_config():
        return {
            'paths': {
                'artifacts': str(tmp_path),
                'processed': str(tmp_path)
            }
        }
    
    monkeypatch.setattr(reporting_module, 'get_config', mock_get_config)
    
    report = generate_confounder_report(mock_df_with_proxies, mock_model)
    
    assert report['status'] == 'computed'
    assert len(report['proxy_variables']) > 0
    assert isinstance(report['r2_delta'], float)
    
    # Check file was written
    artifact_path = tmp_path / 'confounder_report.json'
    assert artifact_path.exists()
    
    with open(artifact_path, 'r') as f:
        saved_report = json.load(f)
    
    assert saved_report['status'] == 'computed'
    assert 'r2_delta' in saved_report

def test_generate_confounder_report_no_proxies(mock_df_without_proxies, mock_model, tmp_path, monkeypatch):
    """Test report generation when proxies are absent."""
    import analysis.reporting as reporting_module
    
    def mock_get_config():
        return {
            'paths': {
                'artifacts': str(tmp_path),
                'processed': str(tmp_path)
            }
        }
    
    monkeypatch.setattr(reporting_module, 'get_config', mock_get_config)
    
    report = generate_confounder_report(mock_df_without_proxies, mock_model)
    
    assert report['status'] == 'N/A'
    assert len(report['proxy_variables']) == 0
    assert report['r2_delta'] is None
    
    # Check file was written
    artifact_path = tmp_path / 'confounder_report.json'
    assert artifact_path.exists()
    
    with open(artifact_path, 'r') as f:
        saved_report = json.load(f)
    
    assert saved_report['status'] == 'N/A'
    assert saved_report['r2_delta'] is None
