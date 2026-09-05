"""
Unit tests for T003: Validation Report Generation.

Tests the logic for determining analysis_mode based on variable availability.
"""
import json
import os
import sys
import pytest
from pathlib import Path
import tempfile
import shutil

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.data.ingest import (
    generate_validation_report,
    check_and_report_variables,
    validate_metadata_variables
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_analysis_mode_error_signal(temp_data_dir):
    """Test that analysis_mode is 'error_signal' when response_correctness exists."""
    metadata = {
        'features': [
            {'name': 'subject_id'},
            {'name': 'stimulus_type'},
            {'name': 'response_correctness'}
        ]
    }
    
    output_path = os.path.join(temp_data_dir, 'validation_report_error_signal.json')
    
    report = generate_validation_report(metadata, output_path, dataset_id="test-ds-1")
    
    assert report['analysis_mode'] == 'error_signal'
    assert report['status'] == 'success'
    assert report['response_correctness_exists'] is True
    
    # Verify file was written
    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        saved_report = json.load(f)
    assert saved_report['analysis_mode'] == 'error_signal'

def test_analysis_mode_stimulus_driven_missing_response(temp_data_dir):
    """Test that analysis_mode is 'stimulus_driven' when only stimulus_type exists."""
    metadata = {
        'features': [
            {'name': 'subject_id'},
            {'name': 'stimulus_type'}
        ]
    }
    
    output_path = os.path.join(temp_data_dir, 'validation_report_stimulus.json')
    
    # This should not raise an error, just log a warning
    report = generate_validation_report(metadata, output_path, dataset_id="test-ds-2")
    
    assert report['analysis_mode'] == 'stimulus_driven'
    assert report['status'] == 'success'
    assert report['response_correctness_exists'] is False
    assert report['stimulus_type_exists'] is True

def test_analysis_mode_stimulus_driven_missing_stimulus(temp_data_dir):
    """Test that analysis_mode is 'stimulus_driven' when only response_correctness exists (should be error_signal actually)."""
    # Correction: If response_correctness exists, it should be error_signal regardless of stimulus_type
    metadata = {
        'features': [
            {'name': 'subject_id'},
            {'name': 'response_correctness'}
        ]
    }
    
    output_path = os.path.join(temp_data_dir, 'validation_report_correctness_only.json')
    
    report = generate_validation_report(metadata, output_path, dataset_id="test-ds-3")
    
    assert report['analysis_mode'] == 'error_signal'
    assert report['status'] == 'success'

def test_analysis_mode_stimulus_driven_missing_both(temp_data_dir):
    """Test that an error is raised when neither variable exists."""
    metadata = {
        'features': [
            {'name': 'subject_id'},
            {'name': 'trial_number'}
        ]
    }
    
    output_path = os.path.join(temp_data_dir, 'validation_report_fail.json')
    
    with pytest.raises(ValueError, match="Critical variables missing"):
        generate_validation_report(metadata, output_path, dataset_id="test-ds-4")

def test_generate_validation_report_creates_file(temp_data_dir):
    """Test that the validation report file is actually created on disk."""
    metadata = {
        'features': [
            {'name': 'subject_id'},
            {'name': 'stimulus_type'},
            {'name': 'response_correctness'}
        ]
    }
    
    output_path = os.path.join(temp_data_dir, 'validation_report_file_check.json')
    
    generate_validation_report(metadata, output_path, dataset_id="test-ds-5")
    
    assert os.path.exists(output_path)
    assert os.path.isfile(output_path)
    
    with open(output_path, 'r') as f:
        content = json.load(f)
        
    assert 'analysis_mode' in content
    assert content['analysis_mode'] in ['error_signal', 'stimulus_driven']

def test_check_and_report_variables():
    """Test the variable checking helper function."""
    # Case 1: Both exist
    metadata_both = {
        'features': [
            {'name': 'stimulus_type'},
            {'name': 'response_correctness'}
        ]
    }
    status = check_and_report_variables(metadata_both)
    assert status['stimulus_type_exists'] is True
    assert status['response_correctness_exists'] is True
    
    # Case 2: Only stimulus
    metadata_stim = {
        'features': [{'name': 'stimulus_type'}]
    }
    status = check_and_report_variables(metadata_stim)
    assert status['stimulus_type_exists'] is True
    assert status['response_correctness_exists'] is False
    
    # Case 3: Only correctness
    metadata_corr = {
        'features': [{'name': 'response_correctness'}]
    }
    status = check_and_report_variables(metadata_corr)
    assert status['stimulus_type_exists'] is False
    assert status['response_correctness_exists'] is True
    
    # Case 4: None
    metadata_none = {
        'features': [{'name': 'other_var'}]
    }
    status = check_and_report_variables(metadata_none)
    assert status['stimulus_type_exists'] is False
    assert status['response_correctness_exists'] is False
    
    # Case 5: Empty metadata
    status = check_and_report_variables({})
    assert status['stimulus_type_exists'] is False
    assert status['response_correctness_exists'] is False