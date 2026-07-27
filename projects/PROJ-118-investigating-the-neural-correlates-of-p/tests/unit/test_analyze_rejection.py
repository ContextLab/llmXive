import pytest
from pathlib import Path
import tempfile
import os

from analyze_rejection import (
    parse_ica_log,
    analyze_rejection_rates,
    identify_excluded_participants,
    write_exclusion_log
)

def test_parse_ica_log_valid():
    """Test parsing a valid ICA log file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Processing subject sub-01\n")
        f.write("Total epochs: 100\n")
        f.write("Rejected epochs: 15\n")
        f.write("Components removed: 2\n")
        f.close()
        
        result = parse_ica_log(Path(f.name))
        
        assert result['total_epochs'] == 100
        assert result['rejected_epochs'] == 15
        assert result['components_removed'] == 2
        
        os.unlink(f.name)

def test_parse_ica_log_empty():
    """Test parsing an empty or unreadable log file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("No relevant data here\n")
        f.close()
        
        result = parse_ica_log(Path(f.name))
        
        assert result['total_epochs'] == 0
        assert result['rejected_epochs'] == 0
        assert result['components_removed'] == 0
        
        os.unlink(f.name)

def test_analyze_rejection_rates():
    """Test analysis across multiple log files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test log files
        log1 = Path(tmpdir) / "ica_log_sub-01.txt"
        log1.write_text("Total epochs: 100\nRejected epochs: 10\nComponents removed: 1\n")
        
        log2 = Path(tmpdir) / "ica_log_sub-02.txt"
        log2.write_text("Total epochs: 200\nRejected epochs: 120\nComponents removed: 3\n")
        
        results = analyze_rejection_rates([log1, log2])
        
        assert 'sub-01' in results
        assert 'sub-02' in results
        assert results['sub-01']['rejection_rate'] == 0.10
        assert results['sub-02']['rejection_rate'] == 0.60

def test_identify_excluded_participants():
    """Test identification of participants exceeding threshold."""
    data = {
        'sub-01': {'total_epochs': 100, 'rejected_epochs': 10, 'rejection_rate': 0.10, 'components_removed': 1},
        'sub-02': {'total_epochs': 200, 'rejected_epochs': 120, 'rejection_rate': 0.60, 'components_removed': 3},
        'sub-03': {'total_epochs': 150, 'rejected_epochs': 75, 'rejection_rate': 0.50, 'components_removed': 2}
    }
    
    excluded = identify_excluded_participants(data, threshold=0.5)
    
    assert 'sub-02' in excluded
    assert 'sub-01' not in excluded
    assert 'sub-03' not in excluded  # Exactly at threshold, not excluded

def test_write_exclusion_log():
    """Test writing exclusion log to file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_exclusion.log"
        
        excluded = {'sub-02', 'sub-04'}
        write_exclusion_log(excluded, output_path)
        
        assert output_path.exists()
        
        content = output_path.read_text()
        assert 'sub-02' in content
        assert 'sub-04' in content
        assert 'Excluded Participants Log' in content
        assert '50%' in content  # Threshold mentioned in header