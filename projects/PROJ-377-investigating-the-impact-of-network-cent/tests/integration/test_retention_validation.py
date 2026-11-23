import os
import json
import pytest
from pathlib import Path
import pandas as pd

from data.retention_validation import (
    load_retention_metrics,
    validate_retention_threshold,
    generate_exclusion_log,
    run_retention_validation
)

@pytest.fixture
def temp_metadata(tmp_path):
    """Create a temporary metadata file for testing."""
    data = {
        'subject_id': ['sub-001', 'sub-002', 'sub-003', 'sub-004', 'sub-005'],
        'pre_motor_score': [45.2, 38.7, 51.0, 42.5, None],
        'post_motor_score': [52.1, 44.3, 58.2, 49.8, 45.6],
        'age': [24, 31, 22, 28, 35],
        'sex': ['M', 'F', 'M', 'F', 'M'],
        'motion_flag': [False, False, False, False, False]
    }
    df = pd.DataFrame(data)
    metadata_path = tmp_path / "metadata.csv"
    df.to_csv(metadata_path, index=False)
    return metadata_path

@pytest.fixture
def temp_metadata_with_motion(tmp_path):
    """Create a temporary metadata file with motion artifacts."""
    data = {
        'subject_id': ['sub-001', 'sub-002', 'sub-003', 'sub-004', 'sub-005'],
        'pre_motor_score': [45.2, 38.7, 51.0, 42.5, 39.1],
        'post_motor_score': [52.1, 44.3, 58.2, 49.8, 45.6],
        'age': [24, 31, 22, 28, 35],
        'sex': ['M', 'F', 'M', 'F', 'M'],
        'motion_flag': [False, True, False, False, True]
    }
    df = pd.DataFrame(data)
    metadata_path = tmp_path / "metadata_motion.csv"
    df.to_csv(metadata_path, index=False)
    return metadata_path

def test_load_retention_metrics_basic(temp_metadata):
    """Test loading retention metrics from a basic metadata file."""
    total, retained, rate, reasons = load_retention_metrics(temp_metadata)
    
    assert total == 5
    assert retained == 4
    assert abs(rate - 0.8) < 1e-6
    assert len(reasons) == 1
    assert reasons[0][0] == 'sub-005'
    assert 'missing_behavioral_data' in reasons[0][1]

def test_load_retention_metrics_with_motion(temp_metadata_with_motion):
    """Test loading retention metrics with motion artifacts."""
    total, retained, rate, reasons = load_retention_metrics(temp_metadata_with_motion)
    
    assert total == 5
    assert retained == 3
    assert abs(rate - 0.6) < 1e-6
    assert len(reasons) == 2
    motion_subjects = [r[0] for r in reasons if 'motion_artifacts' in r[1]]
    assert 'sub-002' in motion_subjects
    assert 'sub-005' in motion_subjects

def test_validate_retention_threshold_pass():
    """Test that validation passes when retention is above threshold."""
    result = validate_retention_threshold(0.85, 100, 85, [])
    assert result is True

def test_validate_retention_threshold_missing_behavioral():
    """Test that validation fails when retention is low due to missing behavioral data."""
    excluded_reasons = [('sub-001', 'missing_behavioral_data')] * 25
    
    with pytest.raises(SystemExit) as excinfo:
        validate_retention_threshold(0.75, 100, 75, excluded_reasons)
    
    assert 'Fatal: Retention < 80% due to missing behavioral data' in str(excinfo.value)

def test_validate_retention_threshold_motion_warning():
    """Test that validation proceeds with warning when retention is low due to motion."""
    excluded_reasons = [('sub-001', 'motion_artifacts')] * 25
    
    result = validate_retention_threshold(0.75, 100, 75, excluded_reasons)
    assert result is True

def test_generate_exclusion_log(tmp_path):
    """Test generating exclusion log."""
    excluded_reasons = [
        ('sub-001', 'missing_behavioral_data'),
        ('sub-002', 'motion_artifacts'),
        ('sub-003', 'missing_behavioral_data; motion_artifacts')
    ]
    
    log_path = tmp_path / "exclusion_log.csv"
    generate_exclusion_log(excluded_reasons, log_path)
    
    assert log_path.exists()
    df = pd.read_csv(log_path)
    assert len(df) == 3
    assert list(df.columns) == ['subject_id', 'exclusion_reason']

def test_run_retention_validation(tmp_path):
    """Test the full retention validation workflow."""
    # Create test metadata
    data = {
        'subject_id': [f'sub-{i:03d}' for i in range(1, 101)],
        'pre_motor_score': [45.0 + i * 0.1 for i in range(100)],
        'post_motor_score': [52.0 + i * 0.1 for i in range(100)],
        'age': [25 + i % 10 for i in range(100)],
        'sex': ['M' if i % 2 == 0 else 'F' for i in range(100)],
        'motion_flag': [False] * 100
    }
    
    # Introduce some missing data
    for i in [10, 20, 30, 40, 50]:
        data['pre_motor_score'][i] = None
    
    metadata_path = tmp_path / "test_metadata.csv"
    pd.DataFrame(data).to_csv(metadata_path, index=False)
    
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    metrics = run_retention_validation(metadata_path, output_dir)
    
    assert 'retention_rate' in metrics
    assert 'total_subjects' in metrics
    assert 'retained_subjects' in metrics
    assert metrics['total_subjects'] == 100
    assert metrics['retained_subjects'] == 95
    assert abs(metrics['retention_rate'] - 0.95) < 1e-6
    
    # Check that output files were created
    metrics_path = output_dir / "retention_metrics.json"
    assert metrics_path.exists()
    
    log_path = output_dir / ".." / "logs" / "exclusion_log.csv"
    assert log_path.exists()