"""
Tests for extended_budget_analysis.py (Task T036)
"""
import os
import sys
import csv
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from extended_budget_analysis import load_csv_file, analyze_budget_exhaustion, write_report

@pytest.fixture
def temp_csv_files():
    """Create temporary CSV files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create primary log with timeouts
        primary_path = tmpdir_path / "execution_log.csv"
        with open(primary_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['instance_id', 'convergence_status', 'turns_to_converge'])
            writer.writeheader()
            # 5 timeouts
            for i in range(5):
                writer.writerow({
                    'instance_id': f'p{i}',
                    'convergence_status': 'timeout',
                    'turns_to_converge': '50'
                })
            # 3 successes
            for i in range(5, 8):
                writer.writerow({
                    'instance_id': f'p{i}',
                    'convergence_status': 'success',
                    'turns_to_converge': '20'
                })
        
        # Create extended log
        extended_path = tmpdir_path / "extended_budget_log.csv"
        with open(extended_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['instance_id', 'convergence_status', 'turns_to_converge'])
            writer.writeheader()
            # 4 successes within 1000 turns
            for i in range(4):
                writer.writerow({
                    'instance_id': f'e{i}',
                    'convergence_status': 'success',
                    'turns_to_converge': str(100 + i * 100)
                })
            # 1 success > 1000 turns (should not count)
            writer.writerow({
                'instance_id': 'e4',
                'convergence_status': 'success',
                'turns_to_converge': '1500'
            })
            # 1 failure
            writer.writerow({
                'instance_id': 'e5',
                'convergence_status': 'failure',
                'turns_to_converge': '1000'
            })
        
        yield primary_path, extended_path

def test_load_csv_file(temp_csv_files):
    primary_path, extended_path = temp_csv_files
    data = load_csv_file(primary_path)
    assert len(data) == 8
    assert data[0]['convergence_status'] == 'timeout'

def test_load_csv_file_missing_file():
    with pytest.raises(FileNotFoundError):
        load_csv_file(Path("/nonexistent/path/file.csv"))

def test_analyze_budget_exhaustion(temp_csv_files):
    primary_path, extended_path = temp_csv_files
    
    results = analyze_budget_exhaustion(primary_path, extended_path)
    
    # Expected: 5 timeouts in primary, 4 successes <= 1000 in extended
    assert results['count_primary_timeouts'] == 5
    assert results['count_extended_successes'] == 4
    # Rate = 4 / 5 * 100 = 80%
    assert abs(results['rate'] - 80.0) < 0.01

def test_analyze_budget_exhaustion_no_timeouts(temp_csv_files):
    primary_path, extended_path = temp_csv_files
    
    # Modify primary to have no timeouts
    with open(primary_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['instance_id', 'convergence_status', 'turns_to_converge'])
        writer.writeheader()
        writer.writerow({
            'instance_id': 'p0',
            'convergence_status': 'success',
            'turns_to_converge': '20'
        })
    
    results = analyze_budget_exhaustion(primary_path, extended_path)
    
    assert results['count_primary_timeouts'] == 0
    assert results['rate'] == 0.0
    assert "No timeouts" in results['message']

def test_write_report(temp_csv_files):
    primary_path, extended_path = temp_csv_files
    results = analyze_budget_exhaustion(primary_path, extended_path)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_report.md"
        write_report(results, output_path)
        
        assert output_path.exists()
        content = output_path.read_text()
        
        assert "Extended Budget Analysis Report" in content
        assert "80.00%" in content
        assert "Primary Log Timeouts" in content
        assert "Extended Log Successes" in content
