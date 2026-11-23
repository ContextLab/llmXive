"""
Unit tests for data models (T007).
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.models import Subject, ConnectivityMatrix, ValidationError
from utils.schema_validator import load_schema, validate_record

@pytest.fixture
def valid_subject_data():
    return {
        'subject_id': 'SUBJ001',
        'group': 'musician',
        'years_of_training': 5.5,
        'age': 16.0,
        'sex': 'M',
        'motion_score': 0.5,
        'ses_score': 7.0
    }

@pytest.fixture
def schema_path():
    return Path(__file__).parent.parent.parent / 'contracts' / 'subject.schema.yaml'

def test_subject_creation_valid(valid_subject_data):
    """Test creating a valid Subject."""
    sub = Subject(**valid_subject_data)
    assert sub.subject_id == 'SUBJ001'
    assert sub.group == 'musician'
    assert sub.years_of_training == 5.5
    assert sub.age == 16.0
    assert sub.sex == 'M'
    assert sub.motion_score == 0.5
    assert sub.ses_score == 7.0

def test_subject_invalid_group(valid_subject_data):
    """Test that invalid group raises ValidationError."""
    valid_subject_data['group'] = 'invalid_group'
    with pytest.raises(ValidationError, match="Invalid group"):
        Subject(**valid_subject_data)

def test_subject_negative_years(valid_subject_data):
    """Test that negative years_of_training raises ValidationError."""
    valid_subject_data['years_of_training'] = -1.0
    with pytest.raises(ValidationError, match="years_of_training cannot be negative"):
        Subject(**valid_subject_data)

def test_subject_age_out_of_range(valid_subject_data):
    """Test that age > 120 raises ValidationError."""
    valid_subject_data['age'] = 150.0
    with pytest.raises(ValidationError, match="Invalid age"):
        Subject(**valid_subject_data)

def test_subject_to_dict(valid_subject_data):
    """Test conversion to dictionary."""
    sub = Subject(**valid_subject_data)
    result = sub.to_dict()
    assert result['subject_id'] == 'SUBJ001'
    assert result['group'] == 'musician'
    assert result['years_of_training'] == 5.5

def test_subject_from_dict(valid_subject_data):
    """Test creation from dictionary."""
    sub = Subject.from_dict(valid_subject_data)
    assert sub.subject_id == 'SUBJ001'
    assert sub.group == 'musician'

def test_connectivity_matrix_valid():
    """Test creating a valid ConnectivityMatrix."""
    matrix = np.eye(5) * 0.5
    conn = ConnectivityMatrix(subject_id='SUBJ001', matrix=matrix)
    assert conn.subject_id == 'SUBJ001'
    assert conn.n_rois == 5
    assert conn.atlas == "Schaefer"

def test_connectivity_matrix_not_square():
    """Test that non-square matrix raises ValidationError."""
    matrix = np.array([[0.5, 0.5], [0.5, 0.5], [0.5, 0.5]])
    with pytest.raises(ValidationError, match="matrix must be square"):
        ConnectivityMatrix(subject_id='SUBJ001', matrix=matrix)

def test_connectivity_matrix_clipping():
    """Test that values outside [-1, 1] are clipped."""
    matrix = np.array([[1.5, -1.5], [-1.5, 1.5]])
    conn = ConnectivityMatrix(subject_id='SUBJ001', matrix=matrix)
    assert np.all(conn.matrix >= -1.0)
    assert np.all(conn.matrix <= 1.0)
    assert conn.matrix[0, 0] == 1.0

def test_schema_validation_valid(valid_subject_data, schema_path):
    """Test that valid data passes schema validation."""
    schema = load_schema(schema_path)
    assert validate_record(valid_subject_data, schema) is True

def test_schema_validation_invalid_group(valid_subject_data, schema_path):
    """Test that invalid group fails schema validation."""
    valid_subject_data['group'] = 'invalid'
    schema = load_schema(schema_path)
    assert validate_record(valid_subject_data, schema) is False

def test_create_subjects_from_dataframe():
    """Test creating subjects from a DataFrame."""
    data = {
        'subject_id': ['SUB1', 'SUB2'],
        'group': ['musician', 'non_musician'],
        'years_of_training': [2.0, 0.0],
        'age': [15.0, 16.0],
        'sex': ['M', 'F'],
        'motion_score': [0.1, 0.2],
        'ses_score': [5.0, 6.0]
    }
    df = pd.DataFrame(data)
    subjects = create_subjects_from_dataframe(df)
    assert len(subjects) == 2
    assert subjects[0].subject_id == 'SUB1'
    assert subjects[1].group == 'non_musician'

def test_create_subjects_from_dataframe_invalid():
    """Test that invalid rows in DataFrame raise ValidationError."""
    data = {
        'subject_id': ['SUB1', 'SUB2'],
        'group': ['musician', 'invalid_group'],
        'years_of_training': [2.0, 0.0],
        'age': [15.0, 16.0],
        'sex': ['M', 'F'],
        'motion_score': [0.1, 0.2],
        'ses_score': [5.0, 6.0]
    }
    df = pd.DataFrame(data)
    with pytest.raises(ValidationError):
        create_subjects_from_dataframe(df)