"""
Unit tests for code/data/validate.py
"""
import pytest
from code.data.validate import validate_metadata

def test_validate_metadata_with_required_fields():
    """Test validation passes when required fields are present"""
    metadata = {
        'subject_id': 'sub-01',
        'pre_treatment_score': 15.0,
        'post_treatment_score': 10.0,
        'instrument': 'GAD-7'
    }
    
    result = validate_metadata(metadata)
    assert result is True

def test_validate_metadata_missing_pre_score():
    """Test validation fails when pre_treatment_score is missing"""
    metadata = {
        'subject_id': 'sub-01',
        'post_treatment_score': 10.0,
        'instrument': 'GAD-7'
    }
    
    with pytest.raises(ValueError, match="pre_treatment_score"):
        validate_metadata(metadata)

def test_validate_metadata_missing_post_score():
    """Test validation fails when post_treatment_score is missing"""
    metadata = {
        'subject_id': 'sub-01',
        'pre_treatment_score': 15.0,
        'instrument': 'GAD-7'
    }
    
    with pytest.raises(ValueError, match="post_treatment_score"):
        validate_metadata(metadata)

def test_validate_metadata_invalid_instrument():
    """Test validation fails when instrument is not validated"""
    metadata = {
        'subject_id': 'sub-01',
        'pre_treatment_score': 15.0,
        'post_treatment_score': 10.0,
        'instrument': 'InvalidScale'
    }
    
    with pytest.raises(ValueError, match="validated anxiety scale"):
        validate_metadata(metadata)