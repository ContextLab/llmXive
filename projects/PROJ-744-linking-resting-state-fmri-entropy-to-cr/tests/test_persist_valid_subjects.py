"""
Tests for T007b: persist_valid_subjects.py

Tests verify that:
1. All subjects are correctly extracted from the phenotype file.
2. Excluded subjects are correctly parsed from log files.
3. The set difference logic works correctly.
4. The output CSV is written to the correct location.
"""

import os
import sys
import tempfile
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from persist_valid_subjects import (
    get_all_subjects_from_phenotype,
    parse_excluded_subjects_from_log,
    get_all_subjects_from_logs,
    main
)
from config import Config

@pytest.fixture
def temp_phenotype_file(tmp_path):
    """Create a temporary phenotype CSV file."""
    data = {
        'SubjectID': ['sub-001', 'sub-002', 'sub-003', 'sub-004'],
        'Age': [25, 30, 35, 40],
        'Sex': ['M', 'F', 'M', 'F']
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "Creative_Problem_Solving.csv"
    df.to_csv(file_path, index=False)
    return file_path

@pytest.fixture
def temp_logs_dir(tmp_path):
    """Create a temporary directory with mock log files."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    
    # Mock motion_exclusions.log
    motion_log = logs_dir / "motion_exclusions.log"
    motion_log.write_text(
        "Excluding subject sub-002 due to high motion (FD > 0.2mm)\n"
        "Excluding subject sub-004 due to high motion\n"
    )
    
    # Mock missing_data.log
    missing_log = logs_dir / "missing_data.log"
    missing_log.write_text(
        "Subject sub-003 excluded due to missing data (< 100 frames)\n"
    )
    
    # Mock parcel_quality.log (should not exclude, but flag - but for this test let's say it excludes)
    parcel_log = logs_dir / "parcel_quality.log"
    parcel_log.write_text(
        "Subject sub-005 flagged for high NaN count (>10%)\n" # Note: sub-005 not in phenotype
    )
    
    return logs_dir

def test_get_all_subjects_from_phenotype(temp_phenotype_file):
    """Test extracting subjects from the phenotype file."""
    with patch.object(Config, 'PHENOTYPE_PATH', str(temp_phenotype_file)):
        subjects = get_all_subjects_from_phenotype()
    
    expected = {'sub-001', 'sub-002', 'sub-003', 'sub-004'}
    assert subjects == expected

def test_parse_excluded_subjects_from_log_motion(temp_logs_dir):
    """Test parsing excluded subjects from motion_exclusions.log."""
    log_path = temp_logs_dir / "motion_exclusions.log"
    excluded = parse_excluded_subjects_from_log(log_path)
    
    assert 'sub-002' in excluded
    assert 'sub-004' in excluded
    assert 'sub-001' not in excluded

def test_parse_excluded_subjects_from_log_missing(temp_logs_dir):
    """Test parsing excluded subjects from missing_data.log."""
    log_path = temp_logs_dir / "missing_data.log"
    excluded = parse_excluded_subjects_from_log(log_path)
    
    assert 'sub-003' in excluded

def test_parse_excluded_subjects_from_log_nonexistent():
    """Test parsing from a non-existent log file returns empty set."""
    excluded = parse_excluded_subjects_from_log(Path("/nonexistent/path.log"))
    assert excluded == set()

def test_get_all_subjects_from_logs(temp_logs_dir):
    """Test aggregating exclusions from all logs."""
    # Mock Config.LOG_DIR to point to temp_logs_dir
    with patch.object(Config, 'LOG_DIR', str(temp_logs_dir)):
        excluded = get_all_subjects_from_logs()
    
    # sub-002 and sub-004 from motion, sub-003 from missing
    # sub-005 is flagged but not in phenotype (handled in main logic)
    assert 'sub-002' in excluded
    assert 'sub-004' in excluded
    assert 'sub-003' in excluded

def test_main_integration(temp_phenotype_file, temp_logs_dir, tmp_path):
    """Test the full main() function end-to-end."""
    # Setup paths
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    
    with patch.object(Config, 'PHENOTYPE_PATH', str(temp_phenotype_file)):
        with patch.object(Config, 'LOG_DIR', str(temp_logs_dir)):
            with patch.object(Config, 'PROCESSED_DATA_DIR', str(processed_dir)):
                valid_subjects = main()
    
    # Expected: All {001, 002, 003, 004} - Excluded {002, 003, 004} = {001}
    expected_valid = {'sub-001'}
    assert valid_subjects == expected_valid
    
    # Verify output file exists and content
    output_file = processed_dir / "valid_subjects.csv"
    assert output_file.exists()
    
    df_out = pd.read_csv(output_file)
    assert 'subject_id' in df_out.columns
    assert len(df_out) == 1
    assert df_out.iloc[0]['subject_id'] == 'sub-001'