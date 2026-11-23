import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.verify_snap import (
    get_sorted_network_files,
    load_simulation_results,
    generate_verification_report,
    generate_manual_verification_log
)

@pytest.fixture
def temp_dirs():
    """Create temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        raw_dir = base / 'data' / 'raw'
        results_dir = base / 'results'
        raw_dir.mkdir(parents=True)
        results_dir.mkdir(parents=True)
        
        # Create some mock SNAP files
        (raw_dir / 'snap_1.mtx').touch()
        (raw_dir / 'snap_10.mtx').touch()
        (raw_dir / 'snap_2.mtx').touch()
        (raw_dir / 'other.txt').touch()  # Should be ignored
        
        yield {
            'base': base,
            'raw': raw_dir,
            'results': results_dir
        }

def test_get_sorted_network_files(temp_dirs):
    """Test filtering and sorting of SNAP files."""
    sorted_files = get_sorted_network_files(temp_dirs['raw'])
    # Should be sorted alphabetically: snap_1, snap_10, snap_2
    assert sorted_files == ['snap_1.mtx', 'snap_10.mtx', 'snap_2.mtx']
    assert 'other.txt' not in sorted_files

def test_get_sorted_network_files_empty(temp_dirs):
    """Test behavior when no SNAP files exist."""
    # Remove all files
    for f in temp_dirs['raw'].iterdir():
        f.unlink()
    
    sorted_files = get_sorted_network_files(temp_dirs['raw'])
    assert sorted_files == []

def test_load_simulation_results_valid(temp_dirs):
    """Test loading valid simulation results."""
    sim_data = [
        {"network_id": "snap_1.mtx", "threshold": 0.5, "metrics": {}},
        {"network_id": "snap_2.mtx", "threshold": 0.7, "metrics": {}}
    ]
    
    results_file = temp_dirs['results'] / 'sim_results.json'
    with open(results_file, 'w') as f:
        json.dump(sim_data, f)
    
    results = load_simulation_results(results_file)
    assert "snap_1.mtx" in results
    assert results["snap_1.mtx"]["threshold"] == 0.5
    assert "snap_2.mtx" in results

def test_load_simulation_results_missing_file(temp_dirs):
    """Test handling of missing simulation results file."""
    non_existent = temp_dirs['results'] / 'non_existent.json'
    with pytest.raises(FileNotFoundError):
        load_simulation_results(non_existent)

def test_generate_verification_report(temp_dirs):
    """Test generation of verification report JSON."""
    snap_files = ['snap_1.mtx', 'snap_2.mtx']
    sim_results = {
        'snap_1.mtx': {'threshold': 0.5},
        'snap_2.mtx': {'threshold': 0.8}
    }
    
    output_path = temp_dirs['results'] / 'verification_report.json'
    generate_verification_report(snap_files, sim_results, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        report = json.load(f)
    
    assert 'networks' in report
    assert len(report['networks']) == 2
    assert report['networks'][0]['id'] == 'snap_1.mtx'
    assert report['networks'][0]['threshold'] == 0.5
    assert report['networks'][1]['id'] == 'snap_2.mtx'
    assert report['networks'][1]['threshold'] == 0.8

def test_generate_verification_report_missing_threshold(temp_dirs):
    """Test handling of missing threshold in simulation results."""
    snap_files = ['snap_1.mtx']
    sim_results = {
        'snap_1.mtx': {'metrics': {}}  # No threshold field
    }
    
    output_path = temp_dirs['results'] / 'verification_report.json'
    generate_verification_report(snap_files, sim_results, output_path)
    
    with open(output_path, 'r') as f:
        report = json.load(f)
    
    assert report['networks'][0]['threshold'] is None

def test_generate_manual_verification_log(temp_dirs):
    """Test generation of manual verification log CSV."""
    snap_files = ['snap_1.mtx', 'snap_2.mtx']
    sim_results = {
        'snap_1.mtx': {'threshold': 0.5},
        'snap_2.mtx': {'threshold': 0.8}
    }
    
    output_path = temp_dirs['results'] / 'manual_verification_log.csv'
    generate_manual_verification_log(snap_files, sim_results, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        content = f.read()
    
    lines = content.strip().split('\n')
    assert lines[0] == 'network_id,threshold,verified_by,timestamp'
    assert len(lines) == 3  # Header + 2 data rows
    assert 'snap_1.mtx' in lines[1]
    assert '0.5' in lines[1]

def test_generate_manual_verification_log_fewer_than_5(temp_dirs):
    """Test that manual log includes all files even if fewer than 5."""
    snap_files = ['snap_1.mtx']
    sim_results = {'snap_1.mtx': {'threshold': 0.5}}
    
    output_path = temp_dirs['results'] / 'manual_verification_log.csv'
    generate_manual_verification_log(snap_files, sim_results, output_path)
    
    with open(output_path, 'r') as f:
        content = f.read()
    
    lines = content.strip().split('\n')
    assert len(lines) == 2  # Header + 1 data row
    assert 'snap_1.mtx' in lines[1]