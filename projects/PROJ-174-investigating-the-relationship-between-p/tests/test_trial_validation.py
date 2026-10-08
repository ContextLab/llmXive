import os
import sys
import pandas as pd
import pytest
from pathlib import Path
import yaml
import shutil

# Ensure parent directory is in path
parent_dir = Path(__file__).resolve().parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from analysis.trial_validation import validate_trial_counts, run_validation_pipeline

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory structure for testing."""
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    results_dir = tmp_path / "results"
    results_dir.mkdir(parents=True)
    return tmp_path

@pytest.fixture
def mock_config(temp_data_dir):
    """Create a mock config.yaml in the temp directory."""
    config = {
        "seeds": 42,
        "thresholds": {"low": 0.40, "mid": 0.50, "high": 0.60},
        "paths": {
            "data_raw": "data/raw",
            "data_processed": str(temp_data_dir / "data" / "processed"),
            "results": str(temp_data_dir / "results")
        },
        "aggregation": False,
        "trial_count_threshold": 20
    }
    config_path = temp_data_dir / "config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    # Save original cwd and change to temp dir so load_config finds it
    original_cwd = os.getcwd()
    os.chdir(temp_data_dir)
    
    yield config
    
    os.chdir(original_cwd)

@pytest.fixture
def mock_data_pass(temp_data_dir):
    """Create a mock features.csv where every subject has > 20 trials."""
    df = pd.DataFrame({
        'subject_id': ['S1'] * 25 + ['S2'] * 30,
        'trial_id': list(range(25)) + list(range(30)),
        'pupil_mean': [1.0] * 55
    })
    path = temp_data_dir / "data" / "processed" / "features.csv"
    df.to_csv(path, index=False)
    return path

@pytest.fixture
def mock_data_fail(temp_data_dir):
    """Create a mock features.csv where one subject has < 20 trials."""
    df = pd.DataFrame({
        'subject_id': ['S1'] * 25 + ['S2'] * 15,
        'trial_id': list(range(25)) + list(range(15)),
        'pupil_mean': [1.0] * 40
    })
    path = temp_data_dir / "data" / "processed" / "features.csv"
    df.to_csv(path, index=False)
    return path

def test_validate_trial_counts_pass(mock_data_pass, mock_config):
    """Test validation passes when all subjects have sufficient trials."""
    data_path = str(mock_data_pass)
    result = validate_trial_counts(data_path, mock_config)
    
    assert len(result) == 2
    assert all(result['trial_count'] >= 20)
    assert all(result['validation_status'] == 'PASS')

def test_validate_trial_counts_fail(mock_data_fail, mock_config):
    """Test validation raises RuntimeError when subject has < 20 trials and aggregation is False."""
    data_path = str(mock_data_fail)
    
    with pytest.raises(RuntimeError) as exc_info:
        validate_trial_counts(data_path, mock_config)
    
    assert "Subject S2 has 15 trials" in str(exc_info.value)
    assert "Insufficient trials per subject" in str(exc_info.value)

def test_validate_trial_counts_aggregate(mock_data_fail, mock_config, temp_data_dir):
    """Test validation aggregates across subjects when flag is True."""
    # Update config to enable aggregation
    mock_config['aggregation'] = True
    
    data_path = str(mock_data_fail)
    result = validate_trial_counts(data_path, mock_config)
    
    assert len(result) == 2
    # S2 should have LOW_COUNT_AGGREGATE status
    s2_row = result[result['subject_id'] == 'S2']
    assert s2_row['validation_status'].values[0] == 'LOW_COUNT_AGGREGATE'
    # S1 should be PASS
    s1_row = result[result['subject_id'] == 'S1']
    assert s1_row['validation_status'].values[0] == 'PASS'

def test_missing_subject_id_column(temp_data_dir, mock_config):
    """Test validation fails if subject_id column is missing."""
    df = pd.DataFrame({
        'trial_id': [1, 2, 3],
        'pupil_mean': [1.0, 1.0, 1.0]
    })
    path = temp_data_dir / "data" / "processed" / "features.csv"
    df.to_csv(path, index=False)
    
    with pytest.raises(ValueError) as exc_info:
        validate_trial_counts(str(path), mock_config)
    
    assert "subject_id" in str(exc_info.value)

def test_run_validation_pipeline_creates_log(mock_data_pass, mock_config, temp_data_dir):
    """Test that run_validation_pipeline creates the log file."""
    # We need to monkeypatch load_config to return our mock config
    import analysis.trial_validation as tv_module
    original_load_config = tv_module.load_config
    
    def mock_load_config():
        return mock_config
    
    tv_module.load_config = mock_load_config
    
    try:
        run_validation_pipeline()
        
        log_path = os.path.join(mock_config['paths']['results'], 'trial_validation.log')
        assert os.path.exists(log_path)
        
        with open(log_path, 'r') as f:
            content = f.read()
            assert "Trial Validation Log" in content
            assert "Validation Results:" in content
    finally:
        tv_module.load_config = original_load_config