import os
import tempfile
from pathlib import Path
import pytest

from analyze_rejection import (
    find_ica_logs,
    parse_ica_log,
    analyze_rejection_rates,
    identify_excluded_participants,
    write_exclusion_log,
    run_rejection_analysis
)

@pytest.fixture
def temp_processed_dir(tmp_path):
    """Create a temporary processed directory with mock ICA logs."""
    # Create sub-01 log
    sub01_log = tmp_path / "sub-01_ica_log.txt"
    sub01_log.write_text("""
    MNE-Python preprocessing log
    ...
    Creating 200 epochs
    ...
    Dropped 10 epoch(s): bad segments
    ...
    Removing 1 component: blink
    """)

    # Create sub-02 log (high rejection)
    sub02_log = tmp_path / "sub-02_ica_log.txt"
    sub02_log.write_text("""
    MNE-Python preprocessing log
    ...
    Creating 200 epochs
    ...
    Dropped 150 epoch(s): bad segments
    ...
    Removing 2 components: blink, muscle
    """)

    # Create sub-03 log (no rejections)
    sub03_log = tmp_path / "sub-03_ica_log.txt"
    sub03_log.write_text("""
    MNE-Python preprocessing log
    ...
    Creating 200 epochs
    ...
    Removing 1 component: blink
    """)

    # Create a non-subject file to test filtering
    other_log = tmp_path / "misc_log.txt"
    other_log.write_text("Some other log")

    return tmp_path

def test_find_ica_logs(temp_processed_dir):
    logs = find_ica_logs(temp_processed_dir)
    # Should find sub-01, sub-02, sub-03 logs but not misc_log.txt
    assert len(logs) == 3
    names = {log.name for log in logs}
    assert "sub-01_ica_log.txt" in names
    assert "sub-02_ica_log.txt" in names
    assert "sub-03_ica_log.txt" in names

def test_parse_ica_log_sub01(temp_processed_dir):
    log_path = temp_processed_dir / "sub-01_ica_log.txt"
    stats = parse_ica_log(log_path)
    assert stats['total_epochs'] == 200
    assert stats['rejected_epochs'] == 10
    assert stats['removed_components'] == 1

def test_parse_ica_log_sub02(temp_processed_dir):
    log_path = temp_processed_dir / "sub-02_ica_log.txt"
    stats = parse_ica_log(log_path)
    assert stats['total_epochs'] == 200
    assert stats['rejected_epochs'] == 150
    assert stats['removed_components'] == 2

def test_parse_ica_log_sub03(temp_processed_dir):
    log_path = temp_processed_dir / "sub-03_ica_log.txt"
    stats = parse_ica_log(log_path)
    assert stats['total_epochs'] == 200
    assert stats['rejected_epochs'] == 0
    assert stats['removed_components'] == 1

def test_analyze_rejection_rates(temp_processed_dir):
    logs = find_ica_logs(temp_processed_dir)
    analysis = analyze_rejection_rates(logs)
    
    assert "sub-01" in analysis
    assert analysis["sub-01"]["rejection_rate"] == 10 / 200
    assert analysis["sub-01"]["rejected_epochs"] == 10

    assert "sub-02" in analysis
    assert analysis["sub-02"]["rejection_rate"] == 150 / 200
    assert analysis["sub-02"]["rejected_epochs"] == 150

    assert "sub-03" in analysis
    assert analysis["sub-03"]["rejection_rate"] == 0 / 200

def test_identify_excluded_participants(temp_processed_dir):
    logs = find_ica_logs(temp_processed_dir)
    analysis = analyze_rejection_rates(logs)
    
    # Threshold 0.5 (50%)
    excluded = identify_excluded_participants(analysis, threshold=0.5)
    
    assert "sub-02" in excluded  # 75% rejection
    assert "sub-01" not in excluded  # 5% rejection
    assert "sub-03" not in excluded  # 0% rejection

def test_write_exclusion_log(temp_processed_dir):
    logs = find_ica_logs(temp_processed_dir)
    analysis = analyze_rejection_rates(logs)
    excluded = identify_excluded_participants(analysis, threshold=0.5)
    
    output_path = temp_processed_dir / "rejected_participants.log"
    write_exclusion_log(excluded, output_path)
    
    assert output_path.exists()
    content = output_path.read_text()
    assert "sub-02" in content
    assert "sub-01" not in content
    assert "# Reason: Rejection rate > 50%" in content

def test_run_rejection_analysis(temp_processed_dir):
    analysis, excluded, log_path = run_rejection_analysis(temp_processed_dir, threshold=0.5)
    
    assert log_path.exists()
    assert "sub-02" in excluded
    assert len(excluded) == 1
    
    content = log_path.read_text()
    assert "sub-02" in content

def test_run_rejection_analysis_empty_dir(tmp_path):
    """Test behavior when no logs are found."""
    analysis, excluded, log_path = run_rejection_analysis(tmp_path, threshold=0.5)
    
    assert log_path.exists()
    assert len(excluded) == 0
    assert len(analysis) == 0
    
    content = log_path.read_text()
    assert "# Excluded Participants" in content