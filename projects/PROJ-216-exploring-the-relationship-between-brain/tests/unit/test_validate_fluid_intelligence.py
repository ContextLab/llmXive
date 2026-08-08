import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
code_path = Path(__file__).parent.parent / 'code'
sys.path.insert(0, str(code_path))

from validate_fluid_intelligence import (
    load_aggregated_subjects,
    extract_behavioral_scores,
    validate_fluid_intelligence,
    write_validation_log
)

@pytest.fixture
def sample_subjects():
    """Sample subjects data with Fluid Intelligence scores."""
    return [
        {
            'id': 'sub-001',
            'age': 25,
            'gender': 'M',
            'behavioral_scores': [
                {'source_type': 'Fluid Intelligence', 'value': 110.5, 'source': 'test'}
            ]
        },
        {
            'id': 'sub-002',
            'age': 30,
            'gender': 'F',
            'behavioral_scores': [
                {'source_type': 'Fluid Intelligence', 'value': 105.0, 'source': 'test'}
            ]
        },
        {
            'id': 'sub-003',
            'age': 22,
            'gender': 'M',
            'behavioral_scores': [
                {'source_type': 'Other Score', 'value': 50.0, 'source': 'test'}
            ]
        }
    ]

@pytest.fixture
def sample_subjects_no_fluid():
    """Sample subjects data without Fluid Intelligence scores."""
    return [
        {
            'id': 'sub-004',
            'age': 28,
            'gender': 'F',
            'behavioral_scores': [
                {'source_type': 'Other Score', 'value': 50.0, 'source': 'test'}
            ]
        },
        {
            'id': 'sub-005',
            'age': 35,
            'gender': 'M',
            'behavioral_scores': []
        }
    ]

def test_extract_behavioral_scores_with_fluid(sample_subjects):
    """Test extraction of subjects with Fluid Intelligence scores."""
    result = extract_behavioral_scores(sample_subjects)
    assert len(result) == 2
    ids = [s['id'] for s in result]
    assert 'sub-001' in ids
    assert 'sub-002' in ids
    assert 'sub-003' not in ids

def test_extract_behavioral_scores_no_fluid(sample_subjects_no_fluid):
    """Test extraction when no Fluid Intelligence scores exist."""
    result = extract_behavioral_scores(sample_subjects_no_fluid)
    assert len(result) == 0

def test_validate_fluid_intelligence_success(sample_subjects):
    """Test successful validation with Fluid Intelligence scores present."""
    result = validate_fluid_intelligence(sample_subjects)
    assert result['validation_passed'] is True
    assert result['subjects_with_fluid_intelligence'] == 2
    assert result['total_subjects'] == 3

def test_validate_fluid_intelligence_failure(sample_subjects_no_fluid):
    """Test validation failure when no Fluid Intelligence scores exist."""
    with pytest.raises(ValueError, match="No valid Fluid Intelligence data found"):
        validate_fluid_intelligence(sample_subjects_no_fluid)

def test_load_aggregated_subjects(tmp_path):
    """Test loading aggregated subjects from a JSON file."""
    data = {'subjects': [{'id': 'test', 'behavioral_scores': []}]}
    file_path = tmp_path / 'test.json'
    with open(file_path, 'w') as f:
        json.dump(data, f)
    
    result = load_aggregated_subjects(str(file_path))
    assert len(result) == 1
    assert result[0]['id'] == 'test'

def test_load_aggregated_subjects_file_not_found():
    """Test loading from a non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_aggregated_subjects('/nonexistent/path/file.json')

def test_write_validation_log(tmp_path):
    """Test writing validation results to a log file."""
    result = {
        'total_subjects': 10,
        'subjects_with_fluid_intelligence': 5,
        'validation_passed': True,
        'subject_ids': ['sub-001', 'sub-002']
    }
    output_path = tmp_path / 'validation_log.json'
    
    write_validation_log(result, str(output_path))
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        loaded = json.load(f)
    assert loaded == result