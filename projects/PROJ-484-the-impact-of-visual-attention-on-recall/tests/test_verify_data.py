"""
Unit tests for verify_data.py
"""

import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the functions to test
from verify_data import (
    load_json_file,
    load_yaml_file,
    find_bids_sidecars,
    extract_columns_from_sidecar,
    verify_dataset_variables
)

def test_load_json_file_valid():
    """Test loading a valid JSON file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({'columns': [{'name': 'x'}, {'name': 'y'}]}, f)
        temp_path = Path(f.name)
    
    try:
        data = load_json_file(temp_path)
        assert 'columns' in data
        assert len(data['columns']) == 2
    finally:
        temp_path.unlink()

def test_load_json_file_invalid():
    """Test loading an invalid JSON file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('invalid json {')
        temp_path = Path(f.name)
    
    try:
        data = load_json_file(temp_path)
        assert data == {}
    finally:
        temp_path.unlink()

def test_extract_columns_from_sidecar():
    """Test extracting columns from a BIDS sidecar."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            'columns': [
                {'name': 'x'},
                {'name': 'y'},
                {'name': 'timestamp'},
                {'name': 'valence'},
                {'name': 'recall'},
                {'name': 'STAI'}
            ]
        }, f)
        temp_path = Path(f.name)
    
    try:
        columns = extract_columns_from_sidecar(temp_path)
        assert 'x' in columns
        assert 'y' in columns
        assert 'timestamp' in columns
        assert 'valence' in columns
        assert 'recall' in columns
        assert 'STAI' in columns
    finally:
        temp_path.unlink()

def test_verify_dataset_variables_all_present():
    """Test verification when all variables are present."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        
        # Create a sidecar with all required variables
        sidecar = data_dir / 'sub-01' / 'func' / 'sub-01_task-rsvp_events.json'
        sidecar.parent.mkdir(parents=True, exist_ok=True)
        
        with open(sidecar, 'w') as f:
            json.dump({
                'columns': [
                    {'name': 'x'},
                    {'name': 'y'},
                    {'name': 'timestamp'},
                    {'name': 'valence'},
                    {'name': 'recall'},
                    {'name': 'STAI'}
                ]
            }, f)
        
        results = verify_dataset_variables(data_dir, 'test_dataset')
        
        assert results['success'] is True
        assert len(results['missing_variables']) == 0
        assert 'x' in results['found_variables']['eye_tracking']
        assert 'valence' in results['found_variables']['stimulus']
        assert 'recall' in results['found_variables']['behavioral']

def test_verify_dataset_variables_missing_vars():
    """Test verification when some variables are missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        
        # Create a sidecar with missing variables
        sidecar = data_dir / 'sub-01' / 'func' / 'sub-01_task-rsvp_events.json'
        sidecar.parent.mkdir(parents=True, exist_ok=True)
        
        with open(sidecar, 'w') as f:
            json.dump({
                'columns': [
                    {'name': 'x'},
                    {'name': 'y'}
                    # Missing timestamp, valence, recall, STAI
                ]
            }, f)
        
        results = verify_dataset_variables(data_dir, 'test_dataset')
        
        assert results['success'] is False
        assert len(results['missing_variables']) > 0
        assert any('timestamp' in v for v in results['missing_variables'])
        assert any('valence' in v for v in results['missing_variables'])

def test_verify_dataset_variables_no_sidecars():
    """Test verification when no sidecars are found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        
        # Create empty directory
        results = verify_dataset_variables(data_dir, 'test_dataset')
        
        assert results['success'] is False
        assert any('No BIDS sidecar files found' in v for v in results['missing_variables'])

def test_verify_dataset_variables_dir_not_found():
    """Test verification when directory doesn't exist."""
    results = verify_dataset_variables(Path('/nonexistent/path'), 'test_dataset')
    
    assert results['success'] is False
    assert any('not found' in v for v in results['missing_variables'])