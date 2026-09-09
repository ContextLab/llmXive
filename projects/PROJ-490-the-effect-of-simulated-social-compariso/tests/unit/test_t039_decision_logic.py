import os
import pytest
from pathlib import Path
import logging
import sys

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.download import load_or_generate_data, generate_synthetic_dataset, discover_real_datasets, verify_irb_consent

class MockConfig:
    def __init__(self, real_datasets=None):
        self.real_datasets = real_datasets or []
    
    def get(self, key, default=None):
        if key == 'discovered_real_datasets':
            return self.real_datasets
        return default

# Mock the config and logger for testing
@pytest.fixture
def mock_no_real_data(monkeypatch):
    def mock_discover():
        return []
    monkeypatch.setattr("data.download.discover_real_datasets", mock_discover)
    return mock_discover

@pytest.fixture
def mock_irb_fail(monkeypatch):
    def mock_discover():
        return [{'id': 'test_ds', 'consent_form_url': 'http://bad.com', 'consent_verified': False, 'available_variables': ['all']}]
    def mock_verify(ds):
        return False, "Consent URL invalid"
    monkeypatch.setattr("data.download.discover_real_datasets", mock_discover)
    monkeypatch.setattr("data.download.verify_irb_consent", mock_verify)
    return mock_discover

@pytest.fixture
def mock_vars_missing(monkeypatch):
    def mock_discover():
        return [{'id': 'test_ds', 'consent_form_url': 'http://good.com', 'consent_verified': True, 'available_variables': ['participant_id', 'pre_self_esteem']}] # Missing others
    def mock_verify(ds):
        return True, "Consent OK"
    monkeypatch.setattr("data.download.discover_real_datasets", mock_discover)
    monkeypatch.setattr("data.download.verify_irb_consent", mock_verify)
    return mock_discover

@pytest.fixture
def mock_success(monkeypatch):
    def mock_discover():
        return [{'id': 'test_ds', 'consent_form_url': 'http://good.com', 'consent_verified': True, 'available_variables': ['participant_id', 'pre_self_esteem', 'post_self_esteem', 'comparison_tendency', 'avatar_condition']}]
    def mock_verify(ds):
        return True, "Consent OK"
    monkeypatch.setattr("data.download.discover_real_datasets", mock_discover)
    monkeypatch.setattr("data.download.verify_irb_consent", mock_verify)
    return mock_discover

def test_synthetic_trigger_no_real_data(mock_no_real_data, tmp_path, monkeypatch):
    """Test T039: Synthetic triggered when no real data found."""
    # Mock config to return empty list
    monkeypatch.setattr("data.download.get_config", lambda: MockConfig([]))
    
    data, reason = load_or_generate_data()
    
    assert data is not None, "Data should be generated"
    assert "No real datasets found" in reason
    
    # Check log file
    log_path = Path("logs/data_path_decision.log")
    assert log_path.exists(), "Decision log should be created"
    content = log_path.read_text()
    assert "DECISION: Synthetic Generation Triggered" in content
    assert "No real datasets found" in content

def test_synthetic_trigger_irb_fail(mock_irb_fail, tmp_path, monkeypatch):
    """Test T039: Synthetic triggered when IRB verification fails."""
    monkeypatch.setattr("data.download.get_config", lambda: MockConfig([{'id': 'test_ds', 'consent_form_url': 'http://bad.com', 'consent_verified': False, 'available_variables': ['all']}]))
    
    data, reason = load_or_generate_data()
    
    assert data is not None, "Data should be generated"
    assert "IRB/Consent verification failed" in reason
    
    log_path = Path("logs/data_path_decision.log")
    assert log_path.exists()
    content = log_path.read_text()
    assert "DECISION: Synthetic Generation Triggered" in content
    assert "IRB/Consent verification failed" in content

def test_synthetic_trigger_vars_missing(mock_vars_missing, tmp_path, monkeypatch):
    """Test T039: Synthetic triggered when required variables are missing."""
    monkeypatch.setattr("data.download.get_config", lambda: MockConfig([{'id': 'test_ds', 'consent_form_url': 'http://good.com', 'consent_verified': True, 'available_variables': ['participant_id', 'pre_self_esteem']}]))
    
    data, reason = load_or_generate_data()
    
    assert data is not None, "Data should be generated"
    assert "missing required variables" in reason
    
    log_path = Path("logs/data_path_decision.log")
    assert log_path.exists()
    content = log_path.read_text()
    assert "DECISION: Synthetic Generation Triggered" in content
    assert "missing required variables" in content

def test_real_data_selected_success(mock_success, tmp_path, monkeypatch):
    """Test T039: Real data path selected when all conditions met."""
    monkeypatch.setattr("data.download.get_config", lambda: MockConfig([{'id': 'test_ds', 'consent_form_url': 'http://good.com', 'consent_verified': True, 'available_variables': ['participant_id', 'pre_self_esteem', 'post_self_esteem', 'comparison_tendency', 'avatar_condition']}]))
    
    data, reason = load_or_generate_data()
    
    # In this mock, data is None because we don't actually fetch, but the decision logic is key
    assert data is None, "Data should be None (indicating real data path selected in this mock)"
    assert "Real dataset found" in reason
    
    log_path = Path("logs/data_path_decision.log")
    assert log_path.exists()
    content = log_path.read_text()
    assert "DECISION: Real Data Selected" in content
    assert "Real dataset found" in content

def test_synthetic_generator_ground_truth():
    """Verify T010 synthetic generator produces expected ground truth structure."""
    df = generate_synthetic_dataset(seed=42, n=100)
    
    assert len(df) == 100
    required_cols = {'participant_id', 'pre_self_esteem', 'post_self_esteem', 'comparison_tendency', 'avatar_condition'}
    assert set(df.columns) == required_cols
    
    # Check avatar_condition is 0 or 1
    assert df['avatar_condition'].isin([0, 1]).all()
    
    # Check numerical ranges (approximate)
    assert df['pre_self_esteem'].mean() > 0
    assert df['post_self_esteem'].mean() > 0