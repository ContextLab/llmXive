import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import csv

from src.verify_snap import (
    get_sorted_network_files,
    load_simulation_results,
    generate_verification_report,
    generate_manual_verification_log,
    main
)

@pytest.fixture
def temp_dirs():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        # Create raw directory with mock SNAP files
        raw_dir = tmp_path / 'data' / 'raw'
        raw_dir.mkdir(parents=True)
        (raw_dir / 'snap_001.mtx').touch()
        (raw_dir / 'snap_002.mtx').touch()
        (raw_dir / 'snap_010.mtx').touch()
        (raw_dir / 'random_graph.txt').touch() # Should be ignored

        # Create results directory
        results_dir = tmp_path / 'results'
        results_dir.mkdir()

        yield {
            'root': tmp_path,
            'raw': raw_dir,
            'results': results_dir
        }

def test_get_sorted_network_files(temp_dirs):
    files = get_sorted_network_files(temp_dirs['raw'])
    assert len(files) == 3
    assert files == ['snap_001.mtx', 'snap_002.mtx', 'snap_010.mtx']

def test_get_sorted_network_files_empty(temp_dirs):
    # Remove all files
    for f in temp_dirs['raw'].iterdir():
        f.unlink()
    files = get_sorted_network_files(temp_dirs['raw'])
    assert len(files) == 0

def test_load_simulation_results_valid(temp_dirs):
    results_file = temp_dirs['results'] / 'sim_results.json'
    data = [
        {'network_id': 'snap_001', 'threshold': 0.5},
        {'network_id': 'snap_002', 'threshold': 0.6}
    ]
    with open(results_file, 'w') as f:
        json.dump(data, f)

    loaded = load_simulation_results(results_file)
    assert 'snap_001' in loaded
    assert loaded['snap_001']['threshold'] == 0.5

def test_load_simulation_results_missing_file(temp_dirs):
    with pytest.raises(FileNotFoundError):
        load_simulation_results(temp_dirs['results'] / 'nonexistent.json')

def test_generate_verification_report(temp_dirs):
    sim_data = {
        'snap_001': {'threshold': 0.5},
        'snap_002': {'threshold': 0.6},
        'snap_010': {'threshold': None}
    }
    sorted_files = ['snap_001.mtx', 'snap_002.mtx', 'snap_010.mtx']
    output_path = temp_dirs['results'] / 'verification_report.json'

    generate_verification_report(sorted_files, sim_data, output_path)

    assert output_path.exists()
    with open(output_path, 'r') as f:
        report = json.load(f)

    assert 'networks' in report
    assert len(report['networks']) == 3
    assert report['networks'][0]['id'] == 'snap_001'
    assert report['networks'][0]['threshold'] == 0.5
    assert report['networks'][2]['threshold'] is None

def test_generate_verification_report_missing_threshold(temp_dirs):
    sim_data = {
        'snap_001': {} # Missing threshold key
    }
    sorted_files = ['snap_001.mtx']
    output_path = temp_dirs['results'] / 'verification_report.json'

    generate_verification_report(sorted_files, sim_data, output_path)

    with open(output_path, 'r') as f:
        report = json.load(f)
    
    assert report['networks'][0]['threshold'] is None

def test_generate_manual_verification_log(temp_dirs):
    sim_data = {
        'snap_001': {'threshold': 0.5},
        'snap_002': {'threshold': 0.6},
        'snap_010': {'threshold': 0.7}
    }
    sorted_files = ['snap_001.mtx', 'snap_002.mtx', 'snap_010.mtx']
    output_path = temp_dirs['results'] / 'manual_verification_log.csv'

    generate_manual_verification_log(sorted_files, sim_data, output_path, max_rows=5)

    assert output_path.exists()
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 3
    assert rows[0]['network_id'] == 'snap_001'
    assert rows[0]['threshold'] == '0.5'
    assert rows[0]['verified_by'] == '' # Empty for human
    assert rows[0]['timestamp'] == '' # Empty for human

def test_generate_manual_verification_log_fewer_than_5(temp_dirs):
    # Only 2 files exist
    sorted_files = ['snap_001.mtx', 'snap_002.mtx']
    sim_data = {
        'snap_001': {'threshold': 0.5},
        'snap_002': {'threshold': 0.6}
    }
    output_path = temp_dirs['results'] / 'manual_verification_log.csv'

    generate_manual_verification_log(sorted_files, sim_data, output_path, max_rows=5)

    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2