import os
import sys
import json
import csv
import tempfile
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from preprocessing.motion_flagging import (
    calculate_max_displacement,
    flag_subject_motion,
    get_all_subject_ids,
    run_motion_flagging_pipeline
)

@pytest.fixture
def mock_motion_params():
    """Create mock motion parameters array (time_points x 6)"""
    # 10 time points, 6 motion parameters
    # First 3: translation (mm), Last 3: rotation (radians)
    np.random.seed(42)
    motion = np.random.rand(10, 6) * 0.5  # Small motion
    motion[0, 0] = 2.5  # One large translation to test threshold
    return motion

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create temporary data directory structure"""
    data_dir = tmp_path / "data"
    raw_dir = data_dir / "raw"
    metadata_dir = data_dir / "metadata"
    processed_dir = data_dir / "processed"
    
    raw_dir.mkdir(parents=True)
    metadata_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)
    
    # Create mock subject directory with motion params
    sub_dir = raw_dir / "sub-001"
    sub_dir.mkdir()
    
    # Create mock motion parameters file
    motion_file = sub_dir / "motion_params.txt"
    with open(motion_file, 'w') as f:
        # Write 10 rows of 6 values
        for i in range(10):
            values = [str(v) for v in np.random.rand(6) * 0.5]
            values[0] = "2.5" if i == 0 else values[0]  # Large motion at first time point
            f.write("\t".join(values) + "\n")
    
    # Create motion_params_available.json
    motion_config_file = metadata_dir / "motion_params_available.json"
    with open(motion_config_file, 'w') as f:
        json.dump({"motion_params_available": True}, f)
    
    # Create subject_status.csv
    status_file = metadata_dir / "subject_status.csv"
    with open(status_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['subject_id', 'status', 'exclusion_reason', 'max_displacement_mm'])
        writer.writerow(['001', 'included', '', ''])
    
    return tmp_path / "data"

def test_calculate_max_displacement_small_motion():
    """Test displacement calculation with small motion values"""
    # Create motion params with small values
    motion = np.array([
        [0.1, 0.1, 0.1, 0.01, 0.01, 0.01],  # All small
        [0.2, 0.2, 0.2, 0.02, 0.02, 0.02],
    ])
    
    max_disp = calculate_max_displacement(motion)
    # Translation: 0.6, Rotation: 0.06 * 60 = 3.6, Total: 4.2
    assert max_disp > 0
    assert max_disp < 10  # Should be reasonable

def test_calculate_max_displacement_large_motion():
    """Test displacement calculation with large motion values"""
    # Create motion params with large values
    motion = np.array([
        [3.0, 3.0, 3.0, 0.1, 0.1, 0.1],  # Large translation
    ])
    
    max_disp = calculate_max_displacement(motion)
    # Translation: 9.0, Rotation: 0.3 * 60 = 18.0, Total: 27.0
    assert max_disp > 20

def test_flag_subject_motion_included(temp_data_dir):
    """Test flagging a subject with motion within threshold"""
    # Create mock motion params with small values
    sub_dir = temp_data_dir / "raw" / "sub-002"
    sub_dir.mkdir()
    motion_file = sub_dir / "motion_params.txt"
    with open(motion_file, 'w') as f:
        for i in range(10):
            values = [str(v) for v in np.random.rand(6) * 0.1]  # Very small motion
            f.write("\t".join(values) + "\n")
    
    result = flag_subject_motion("002", motion_available=True)
    
    assert result['subject_id'] == "002"
    assert result['included'] is True
    assert 'within acceptable limits' in result['reason']
    assert result['max_displacement_mm'] is not None

def test_flag_subject_motion_excluded_high_motion(temp_data_dir):
    """Test flagging a subject with motion exceeding threshold"""
    # Create mock motion params with large values
    sub_dir = temp_data_dir / "raw" / "sub-003"
    sub_dir.mkdir()
    motion_file = sub_dir / "motion_params.txt"
    with open(motion_file, 'w') as f:
        for i in range(10):
            values = [str(v) for v in np.random.rand(6) * 0.1]
            values[0] = "3.0"  # Large translation
            f.write("\t".join(values) + "\n")
    
    result = flag_subject_motion("003", motion_available=True)
    
    assert result['subject_id'] == "003"
    assert result['included'] is False
    assert 'exceeds threshold' in result['reason']
    assert result['max_displacement_mm'] is not None
    assert result['max_displacement_mm'] > 2.0

def test_flag_subject_motion_no_params_available(temp_data_dir):
    """Test flagging when motion parameters are not available"""
    result = flag_subject_motion("004", motion_available=False)
    
    assert result['subject_id'] == "004"
    assert result['included'] is False
    assert 'not available' in result['reason']
    assert result['max_displacement_mm'] is None

def test_run_motion_flagging_pipeline(temp_data_dir):
    """Test the full motion flagging pipeline"""
    # Patch the DATA_DIR to use our temp directory
    with patch('preprocessing.motion_flagging.DATA_DIR', temp_data_dir):
        with patch('preprocessing.motion_flagging.METADATA_DIR', temp_data_dir / "metadata"):
            with patch('preprocessing.motion_flagging.RAW_DIR', temp_data_dir / "raw"):
                results = run_motion_flagging_pipeline()
    
    assert len(results) > 0
    
    # Check that subject_status.csv was updated
    status_file = temp_data_dir / "metadata" / "subject_status.csv"
    assert status_file.exists()
    
    with open(status_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) > 0
        
        # Verify at least one subject has status set
        statuses = [row['status'] for row in rows]
        assert any(s in ['included', 'excluded'] for s in statuses)
