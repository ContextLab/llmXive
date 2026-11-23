"""
Unit tests for validate_microbiome_fields module.
"""
import pytest
import tempfile
import os
import json
from pathlib import Path
import pandas as pd

# Mock the logging and config for testing
import sys
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from validate_microbiome_fields import validate_fields, REQUIRED_FIELDS

def test_validate_fields_all_valid():
    """Test validation with all required fields present."""
    data = [
        {'Age': 25, 'Sex': 'M', 'BMI': 22.5, 'Diet': 'Ve'},
        {'Age': 30, 'Sex': 'F', 'BMI': 24.1, 'Diet': 'Om'}
    ]
    
    results = validate_fields(data, REQUIRED_FIELDS)
    
    assert results['total_rows'] == 2
    assert results['valid_rows'] == 2
    assert results['invalid_rows'] == 0
    for field in REQUIRED_FIELDS:
        assert results['missing_fields'][field] == 0

def test_validate_fields_missing_one():
    """Test validation with one missing field."""
    data = [
        {'Age': 25, 'Sex': 'M', 'BMI': 22.5, 'Diet': 'Ve'},
        {'Age': 30, 'Sex': 'F', 'BMI': 24.1}  # Missing Diet
    ]
    
    results = validate_fields(data, REQUIRED_FIELDS)
    
    assert results['total_rows'] == 2
    assert results['valid_rows'] == 1
    assert results['invalid_rows'] == 1
    assert results['missing_fields']['Diet'] == 1

def test_validate_fields_missing_multiple():
    """Test validation with multiple missing fields."""
    data = [
        {'Age': 25, 'Sex': 'M'},  # Missing BMI and Diet
        {'Age': 30, 'BMI': 24.1}  # Missing Sex and Diet
    ]
    
    results = validate_fields(data, REQUIRED_FIELDS)
    
    assert results['total_rows'] == 2
    assert results['valid_rows'] == 0
    assert results['invalid_rows'] == 2
    assert results['missing_fields']['BMI'] == 1
    assert results['missing_fields']['Sex'] == 1
    assert results['missing_fields']['Diet'] == 2

def test_validate_fields_empty_values():
    """Test validation with empty string values."""
    data = [
        {'Age': 25, 'Sex': '', 'BMI': 22.5, 'Diet': 'Ve'},  # Empty Sex
        {'Age': None, 'Sex': 'F', 'BMI': 24.1, 'Diet': 'Om'}  # None Age
    ]
    
    results = validate_fields(data, REQUIRED_FIELDS)
    
    assert results['total_rows'] == 2
    assert results['valid_rows'] == 0
    assert results['invalid_rows'] == 2
    assert results['missing_fields']['Sex'] == 1
    assert results['missing_fields']['Age'] == 1

def test_validate_fields_with_whitespace():
    """Test validation with whitespace-only strings."""
    data = [
        {'Age': 25, 'Sex': '   ', 'BMI': 22.5, 'Diet': 'Ve'}  # Whitespace Sex
    ]
    
    results = validate_fields(data, REQUIRED_FIELDS)
    
    assert results['valid_rows'] == 0
    assert results['invalid_rows'] == 1
    assert results['missing_fields']['Sex'] == 1
