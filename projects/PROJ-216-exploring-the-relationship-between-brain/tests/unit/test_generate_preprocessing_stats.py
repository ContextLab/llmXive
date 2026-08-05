import json
import os
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the module under test
# We assume the test is run from the project root or code directory
# Adjust import based on execution context
sys_path_backup = sys.path.copy()
try:
    code_dir = Path(__file__).resolve().parent.parent.parent / 'code'
    sys.path.insert(0, str(code_dir))
    from generate_preprocessing_stats import load_subject_logs, calculate_stats
finally:
    sys.path = sys_path_backup

def test_calculate_stats_all_success():
    logs = [
        {'subject_id': 'sub-01', 'success': True},
        {'subject_id': 'sub-02', 'success': True},
        {'subject_id': 'sub-03', 'success': True}
    ]
    stats = calculate_stats(logs)
    assert stats['total_subjects'] == 3
    assert stats['successful_subjects'] == 3
    assert stats['success_rate_percentage'] == 100.0

def test_calculate_stats_partial_success():
    logs = [
        {'subject_id': 'sub-01', 'success': True},
        {'subject_id': 'sub-02', 'success': False},
        {'subject_id': 'sub-03', 'success': True}
    ]
    stats = calculate_stats(logs)
    assert stats['total_subjects'] == 3
    assert stats['successful_subjects'] == 2
    assert stats['success_rate_percentage'] == 66.67

def test_calculate_stats_no_success():
    logs = [
        {'subject_id': 'sub-01', 'success': False},
        {'subject_id': 'sub-02', 'success': False}
    ]
    stats = calculate_stats(logs)
    assert stats['total_subjects'] == 2
    assert stats['successful_subjects'] == 0
    assert stats['success_rate_percentage'] == 0.0

def test_calculate_stats_empty():
    logs = []
    stats = calculate_stats(logs)
    assert stats['total_subjects'] == 0
    assert stats['successful_subjects'] == 0
    assert stats['success_rate_percentage'] == 0.0

def test_load_subject_logs(tmp_path):
    # Create temporary log files
    log_dir = tmp_path / 'logs'
    log_dir.mkdir()
    
    # Valid success log
    success_log = log_dir / 'sub-01_preprocess_log.json'
    with open(success_log, 'w') as f:
        json.dump({'subject_id': 'sub-01', 'status': 'success', 'metrics': {}}, f)
    
    # Valid failure log
    fail_log = log_dir / 'sub-02_preprocess_log.json'
    with open(fail_log, 'w') as f:
        json.dump({'subject_id': 'sub-02', 'status': 'failed', 'reason': 'Motion'}, f)
    
    # Malformed log (should be skipped)
    bad_log = log_dir / 'sub-03_preprocess_log.json'
    with open(bad_log, 'w') as f:
        f.write("not valid json")
    
    logs = load_subject_logs(log_dir)
    
    # Should find 2 valid logs (1 success, 1 failure)
    assert len(logs) == 2
    
    # Check success log
    success_entry = next((l for l in logs if l['subject_id'] == 'sub-01'), None)
    assert success_entry is not None
    assert success_entry['success'] is True
    
    # Check failure log
    fail_entry = next((l for l in logs if l['subject_id'] == 'sub-02'), None)
    assert fail_entry is not None
    assert fail_entry['success'] is False