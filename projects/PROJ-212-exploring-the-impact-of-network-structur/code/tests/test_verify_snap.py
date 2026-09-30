import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
import logging

# Add parent directory to path for imports if running directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.verify_snap import (
    get_sorted_network_files,
    load_simulation_results,
    generate_verification_report,
    generate_manual_verification_log
)

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        raw_dir = tmp_path / 'data' / 'raw'
        raw_dir.mkdir(parents=True)
        results_dir = tmp_path / 'results'
        results_dir.mkdir()
        yield {
            'raw_dir': raw_dir,
            'results_dir': results_dir,
            'base': tmp_path
        }

def test_get_sorted_network_files(temp_dirs):
    """Test that network files are correctly identified and sorted."""
    raw_dir = temp_dirs['raw_dir']
    
    # Create some dummy files
    (raw_dir / 'z_network.mtx').touch()
    (raw_dir / 'a_network.csv').touch()
    (raw_dir / 'm_network.gml').touch()
    (raw_dir / 'ignore.txt').touch()
    
    files = get_sorted_network_files(raw_dir)
    
    assert len(files) == 3
    assert files == ['a_network.csv', 'm_network.gml', 'z_network.mtx']

def test_get_sorted_network_files_empty(temp_dirs):
    """Test behavior when no network files exist."""
    files = get_sorted_network_files(temp_dirs['raw_dir'])
    assert files == []

def test_load_simulation_results_valid(temp_dirs):
    """Test loading valid simulation results."""
    results_path = temp_dirs['results_dir'] / 'sim_results.json'
    data = [
        {"network_id": "test.mtx", "threshold": 0.5},
        {"id": "test2.csv", "threshold": 0.8}
    ]
    with open(results_path, 'w') as f:
        json.dump(data, f)
    
    loaded = load_simulation_results(results_path)
    assert len(loaded) == 2
    assert loaded[0]['network_id'] == 'test.mtx'
    assert loaded[1]['id'] == 'test2.csv'

def test_load_simulation_results_missing_file(temp_dirs):
    """Test loading when file does not exist."""
    results_path = temp_dirs['results_dir'] / 'nonexistent.json'
    with pytest.raises(FileNotFoundError):
        load_simulation_results(results_path)

def test_generate_verification_report(temp_dirs):
    """Test generation of verification report."""
    sorted_files = ['a.mtx', 'b.csv']
    sim_results = [
        {"network_id": "a.mtx", "threshold": 0.5},
        {"network_id": "b.csv", "threshold": 0.8}
    ]
    output_path = temp_dirs['results_dir'] / 'verification_report.json'
    
    generate_verification_report(sorted_files, sim_results, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        report = json.load(f)
    
    assert 'networks' in report
    assert len(report['networks']) == 2
    assert report['networks'][0]['id'] == 'a.mtx'
    assert report['networks'][0]['threshold'] == 0.5
    assert report['networks'][1]['id'] == 'b.csv'
    assert report['networks'][1]['threshold'] == 0.8

def test_generate_verification_report_missing_threshold(temp_dirs):
    """Test generation when some thresholds are missing."""
    sorted_files = ['a.mtx', 'b.csv']
    sim_results = [
        {"network_id": "a.mtx", "threshold": 0.5}
    ]
    output_path = temp_dirs['results_dir'] / 'verification_report.json'
    
    generate_verification_report(sorted_files, sim_results, output_path)
    
    with open(output_path, 'r') as f:
        report = json.load(f)
    
    assert report['networks'][1]['threshold'] is None

def test_generate_manual_verification_log(temp_dirs):
    """Test generation of manual verification log."""
    sorted_files = ['a.mtx', 'b.csv', 'c.gml', 'd.mtx', 'e.csv', 'f.gml']
    output_path = temp_dirs['results_dir'] / 'manual_verification_log.txt'
    
    generate_manual_verification_log(sorted_files, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        content = f.read()
    
    assert "Manual Verification Log" in content
    assert "a.mtx" in content
    assert "b.csv" in content
    assert "c.gml" in content
    assert "d.mtx" in content
    assert "e.csv" in content
    assert "f.gml" not in content # Only first 5
    assert "Sign-off:" in content

def test_generate_manual_verification_log_fewer_than_5(temp_dirs):
    """Test generation when fewer than 5 files exist."""
    sorted_files = ['a.mtx', 'b.csv']
    output_path = temp_dirs['results_dir'] / 'manual_verification_log.txt'
    
    generate_manual_verification_log(sorted_files, output_path)
    
    with open(output_path, 'r') as f:
        content = f.read()
    
    assert "a.mtx" in content
    assert "b.csv" in content
    assert content.count("Verifier Name:") == 1
