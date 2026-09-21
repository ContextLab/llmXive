import os
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data.retention_validation import (
    load_retention_metrics,
    validate_retention_threshold,
    generate_exclusion_log,
    run_retention_validation
)
from utils.config import Config, OutputPaths, reset_config

@pytest.fixture
def temp_config():
    """Create a temporary config for testing."""
    temp_dir = tempfile.mkdtemp()
    output_paths = OutputPaths(
        retention_metrics_path=os.path.join(temp_dir, 'retention_metrics.json'),
        behavioral_scores_path=os.path.join(temp_dir, 'behavioral', 'subject_scores.csv'),
        exclusion_log_path=os.path.join(temp_dir, 'logs', 'exclusion_log.csv'),
        fd_mean_path=os.path.join(temp_dir, 'behavioral', 'fd_mean.csv')
    )
    config = Config(output_paths=output_paths)
    reset_config()
    # Patch get_config to return our test config
    with patch('data.retention_validation.get_config', return_value=config):
        yield config, temp_dir
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)

def test_validate_retention_threshold():
    """Test retention threshold validation logic."""
    assert validate_retention_threshold(0.85, 0.8) is True
    assert validate_retention_threshold(0.8, 0.8) is True
    assert validate_retention_threshold(0.79, 0.8) is False
    assert validate_retention_threshold(0.5, 0.8) is False

def test_generate_exclusion_log_missing_data(temp_config):
    """Test exclusion log generation for missing behavioral data."""
    config, _ = temp_config
    
    # Create test behavioral data with missing values
    behavioral_data = pd.DataFrame({
        'subject_id': ['sub-001', 'sub-002', 'sub-003', 'sub-004'],
        'pre_motor_score': [10.0, 12.0, None, 15.0],
        'post_motor_score': [12.0, None, 18.0, 17.0],
        'age': [25, 30, 28, 35],
        'sex': ['M', 'F', 'M', 'F'],
        'improvement_score': [2.0, None, 6.0, 2.0]
    })
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(config.output_paths.exclusion_log_path), exist_ok=True)
    
    exclusion_df = generate_exclusion_log(behavioral_data, 0.75, config.output_paths.exclusion_log_path)
    
    # Check that exclusion log was created
    assert os.path.exists(config.output_paths.exclusion_log_path)
    
    # Verify excluded subjects
    excluded_ids = set(exclusion_df['subject_id'].tolist())
    assert 'sub-002' in excluded_ids  # Missing post_motor_score and improvement_score
    assert 'sub-003' in excluded_ids  # Missing pre_motor_score
    
    # Verify reasons
    reasons = exclusion_df['reason'].tolist()
    assert any('Missing pre_motor_score' in r for r in reasons)
    assert any('Missing post_motor_score' in r for r in reasons)

def test_generate_exclusion_log_motion_artifacts(temp_config):
    """Test exclusion log generation for motion artifacts."""
    config, _ = temp_config
    
    # Create test behavioral data with high FD
    behavioral_data = pd.DataFrame({
        'subject_id': ['sub-001', 'sub-002', 'sub-003'],
        'pre_motor_score': [10.0, 12.0, 15.0],
        'post_motor_score': [12.0, 14.0, 17.0],
        'fd_mean': [0.1, 0.5, 0.2],  # sub-002 has high motion
        'age': [25, 30, 28],
        'sex': ['M', 'F', 'M']
    })
    
    # Patch config to set FD threshold
    with patch.object(config, 'get_fd_threshold', return_value=0.3):
        os.makedirs(os.path.dirname(config.output_paths.exclusion_log_path), exist_ok=True)
        exclusion_df = generate_exclusion_log(behavioral_data, 0.9, config.output_paths.exclusion_log_path)
    
    # Verify sub-002 was excluded for motion
    assert 'sub-002' in exclusion_df['subject_id'].tolist()
    assert any('Motion artifacts' in r for r in exclusion_df['reason'].tolist())

def test_generate_exclusion_log_no_exclusions(temp_config):
    """Test exclusion log when no subjects are excluded."""
    config, _ = temp_config
    
    # Create complete test data
    behavioral_data = pd.DataFrame({
        'subject_id': ['sub-001', 'sub-002'],
        'pre_motor_score': [10.0, 12.0],
        'post_motor_score': [12.0, 14.0],
        'fd_mean': [0.1, 0.2],
        'age': [25, 30],
        'sex': ['M', 'F'],
        'improvement_score': [2.0, 2.0]
    })
    
    with patch.object(config, 'get_fd_threshold', return_value=0.3):
        os.makedirs(os.path.dirname(config.output_paths.exclusion_log_path), exist_ok=True)
        exclusion_df = generate_exclusion_log(behavioral_data, 1.0, config.output_paths.exclusion_log_path)
    
    # Verify empty exclusion log
    assert len(exclusion_df) == 0
    assert os.path.exists(config.output_paths.exclusion_log_path)

def test_load_retention_metrics_file_not_found():
    """Test that FileNotFoundError is raised when metrics file is missing."""
    with patch('data.retention_validation.get_config') as mock_config:
        mock_config.return_value.output_paths.retention_metrics_path = '/nonexistent/path.json'
        with pytest.raises(FileNotFoundError):
            load_retention_metrics()

def test_run_retention_validation_success(temp_config):
    """Test successful run of retention validation."""
    config, _ = temp_config
    
    # Create retention metrics file
    metrics = {
        'total_subjects': 100,
        'retained_subjects': 85,
        'retention_rate': 0.85
    }
    with open(config.output_paths.retention_metrics_path, 'w') as f:
        json.dump(metrics, f)
    
    # Create behavioral data file
    os.makedirs(os.path.dirname(config.output_paths.behavioral_scores_path), exist_ok=True)
    behavioral_data = pd.DataFrame({
        'subject_id': [f'sub-{i:03d}' for i in range(1, 86)],
        'pre_motor_score': [10.0] * 85,
        'post_motor_score': [12.0] * 85,
        'age': [25] * 85,
        'sex': ['M'] * 85,
        'improvement_score': [2.0] * 85
    })
    behavioral_data.to_csv(config.output_paths.behavioral_scores_path, index=False)
    
    with patch.object(config, 'get_min_retention_rate', return_value=0.8):
        passed, exclusion_df = run_retention_validation()
    
    assert passed is True
    assert os.path.exists(config.output_paths.exclusion_log_path)

def test_run_retention_validation_failure(temp_config):
    """Test retention validation failure when rate is too low."""
    config, _ = temp_config
    
    # Create retention metrics with low rate
    metrics = {
        'total_subjects': 100,
        'retained_subjects': 70,
        'retention_rate': 0.70
    }
    with open(config.output_paths.retention_metrics_path, 'w') as f:
        json.dump(metrics, f)
    
    # Create empty behavioral data
    os.makedirs(os.path.dirname(config.output_paths.behavioral_scores_path), exist_ok=True)
    pd.DataFrame(columns=['subject_id']).to_csv(config.output_paths.behavioral_scores_path, index=False)
    
    with patch.object(config, 'get_min_retention_rate', return_value=0.8):
        passed, exclusion_df = run_retention_validation()
    
    assert passed is False
    assert os.path.exists(config.output_paths.exclusion_log_path)