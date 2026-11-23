"""
Unit tests for the attention check validation module.
"""

import pytest
import csv
import json
import tempfile
from pathlib import Path
from typing import List, Dict, Any

# Import the module under test
from code.validation.attention_check import (
    load_baseline_data,
    calculate_sart_accuracy,
    identify_low_quality_participants,
    load_existing_exclusions,
    save_exclusions,
    append_low_quality_exclusions,
    generate_quality_report,
    run_attention_check_validation,
    SART_ACCURACY_THRESHOLD
)


@pytest.fixture
def sample_baseline_data():
    """Create sample baseline data for testing."""
    return [
        # Participant P001 - High accuracy (should pass)
        {'participant_id': 'P001', 'metric_type': 'sart', 'commission_error': 'False', 'omission_error': 'False'},
        {'participant_id': 'P001', 'metric_type': 'sart', 'commission_error': 'False', 'omission_error': 'False'},
        {'participant_id': 'P001', 'metric_type': 'sart', 'commission_error': 'False', 'omission_error': 'False'},
        {'participant_id': 'P001', 'metric_type': 'sart', 'commission_error': 'False', 'omission_error': 'False'},
        {'participant_id': 'P001', 'metric_type': 'sart', 'commission_error': 'False', 'omission_error': 'False'},
        
        # Participant P002 - Low accuracy (should fail)
        {'participant_id': 'P002', 'metric_type': 'sart', 'commission_error': 'True', 'omission_error': 'False'},
        {'participant_id': 'P002', 'metric_type': 'sart', 'commission_error': 'True', 'omission_error': 'False'},
        {'participant_id': 'P002', 'metric_type': 'sart', 'commission_error': 'True', 'omission_error': 'False'},
        {'participant_id': 'P002', 'metric_type': 'sart', 'commission_error': 'False', 'omission_error': 'False'},
        {'participant_id': 'P002', 'metric_type': 'sart', 'commission_error': 'False', 'omission_error': 'False'},
        
        # Participant P003 - Very low accuracy (should fail)
        {'participant_id': 'P003', 'metric_type': 'sart', 'commission_error': 'True', 'omission_error': 'True'},
        {'participant_id': 'P003', 'metric_type': 'sart', 'commission_error': 'True', 'omission_error': 'True'},
        {'participant_id': 'P003', 'metric_type': 'sart', 'commission_error': 'True', 'omission_error': 'False'},
        {'participant_id': 'P003', 'metric_type': 'sart', 'commission_error': 'False', 'omission_error': 'False'},
        {'participant_id': 'P003', 'metric_type': 'sart', 'commission_error': 'False', 'omission_error': 'False'},
        
        # Non-SART data (should be ignored)
        {'participant_id': 'P001', 'metric_type': 'pss10', 'value': '25'},
        {'participant_id': 'P002', 'metric_type': 'panas', 'value': '30'},
    ]

@pytest.fixture
def temp_baseline_file(sample_baseline_data):
    """Create a temporary baseline data CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.DictWriter(f, fieldnames=sample_baseline_data[0].keys())
        writer.writeheader()
        writer.writerows(sample_baseline_data)
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    temp_path.unlink()

@pytest.fixture
def temp_exclusions_file():
    """Create a temporary exclusions JSON file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({'exclusions': [], 'generated_at': None}, f)
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    temp_path.unlink()

@pytest.fixture
def temp_report_file():
    """Create a temporary report file path."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    temp_path.unlink()

def test_calculate_sart_accuracy_high():
    """Test accuracy calculation for high-performing participant."""
    trials = [
        {'metric_type': 'sart', 'commission_error': 'False', 'omission_error': 'False'},
        {'metric_type': 'sart', 'commission_error': 'False', 'omission_error': 'False'},
        {'metric_type': 'sart', 'commission_error': 'False', 'omission_error': 'False'},
        {'metric_type': 'sart', 'commission_error': 'False', 'omission_error': 'False'},
        {'metric_type': 'sart', 'commission_error': 'False', 'omission_error': 'False'},
    ]
    
    accuracy = calculate_sart_accuracy(trials)
    assert accuracy == 1.0

def test_calculate_sart_accuracy_low():
    """Test accuracy calculation for low-performing participant."""
    trials = [
        {'metric_type': 'sart', 'commission_error': 'True', 'omission_error': 'False'},
        {'metric_type': 'sart', 'commission_error': 'True', 'omission_error': 'False'},
        {'metric_type': 'sart', 'commission_error': 'True', 'omission_error': 'False'},
        {'metric_type': 'sart', 'commission_error': 'False', 'omission_error': 'False'},
        {'metric_type': 'sart', 'commission_error': 'False', 'omission_error': 'False'},
    ]
    
    accuracy = calculate_sart_accuracy(trials)
    # 2 correct out of 5 = 0.4
    assert accuracy == 0.4

def test_calculate_sart_accuracy_no_trials():
    """Test accuracy calculation when no trials are present."""
    trials = []
    accuracy = calculate_sart_accuracy(trials)
    assert accuracy == 0.0

def test_identify_low_quality_participants(temp_baseline_file):
    """Test identification of low-quality participants."""
    data = load_baseline_data(temp_baseline_file)
    low_quality = identify_low_quality_participants(data, threshold=0.5)
    
    assert len(low_quality) == 2  # P002 and P003
    
    participant_ids = {p['participant_id'] for p in low_quality}
    assert 'P002' in participant_ids
    assert 'P003' in participant_ids
    assert 'P001' not in participant_ids

def test_identify_low_quality_participants_all_pass(temp_baseline_file):
    """Test when all participants pass the threshold."""
    data = load_baseline_data(temp_baseline_file)
    low_quality = identify_low_quality_participants(data, threshold=0.3)
    
    assert len(low_quality) == 1  # Only P003 (accuracy 0.2)
    assert low_quality[0]['participant_id'] == 'P003'

def test_load_baseline_data_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        load_baseline_data(Path('/nonexistent/path.csv'))

def test_load_existing_exclusions_empty(temp_exclusions_file):
    """Test loading empty exclusions file."""
    exclusions = load_existing_exclusions(temp_exclusions_file)
    
    assert 'exclusions' in exclusions
    assert len(exclusions['exclusions']) == 0

def test_save_exclusions(temp_exclusions_file):
    """Test saving exclusions to file."""
    test_data = {
        'exclusions': [
            {'participant_id': 'P001', 'reason': 'test'}
        ],
        'generated_at': '2024-01-01'
    }
    
    save_exclusions(test_data, temp_exclusions_file)
    
    with open(temp_exclusions_file, 'r') as f:
        loaded = json.load(f)
    
    assert len(loaded['exclusions']) == 1
    assert loaded['exclusions'][0]['participant_id'] == 'P001'

def test_append_low_quality_exclusions(temp_baseline_file, temp_exclusions_file):
    """Test appending low quality exclusions to existing file."""
    data = load_baseline_data(temp_baseline_file)
    low_quality = identify_low_quality_participants(data, threshold=0.5)
    
    # First append
    append_low_quality_exclusions(low_quality, temp_exclusions_file)
    
    # Load and verify
    with open(temp_exclusions_file, 'r') as f:
        exclusions = json.load(f)
    
    assert len(exclusions['exclusions']) == 2
    
    # Second append (same data)
    append_low_quality_exclusions(low_quality, temp_exclusions_file)
    
    # Load and verify (should have 4 now)
    with open(temp_exclusions_file, 'r') as f:
        exclusions = json.load(f)
    
    assert len(exclusions['exclusions']) == 4

def test_generate_quality_report(temp_baseline_file, temp_report_file):
    """Test quality report generation."""
    data = load_baseline_data(temp_baseline_file)
    low_quality = identify_low_quality_participants(data, threshold=0.5)
    
    generate_quality_report(low_quality, temp_report_file)
    
    with open(temp_report_file, 'r') as f:
        content = f.read()
    
    assert '# Data Quality Report' in content
    assert 'P002' in content
    assert 'P003' in content
    assert 'low_sart_accuracy' in content

def test_run_attention_check_validation(temp_baseline_file, temp_exclusions_file, temp_report_file):
    """Test the complete validation pipeline."""
    results = run_attention_check_validation(
        baseline_path=temp_baseline_file,
        exclusions_path=temp_exclusions_file,
        report_path=temp_report_file,
        threshold=0.5
    )
    
    assert 'total_participants_checked' in results
    assert 'low_quality_count' in results
    assert results['low_quality_count'] == 2
    assert results['threshold'] == 0.5
    
    # Verify files were created
    assert temp_exclusions_file.exists()
    assert temp_report_file.exists()