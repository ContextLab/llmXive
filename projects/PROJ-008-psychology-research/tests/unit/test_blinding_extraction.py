import pytest
from code.data.extractor import extract_blinding_status

def test_extract_blinded():
    """Test extraction of blinded study."""
    study = {
        "id": "test-blinded",
        "rater_type": "blinded",
        "blinded_assessment_flag": True
    }
    result = extract_blinding_status(study)
    assert result["rater_type"] == "blinded"
    assert result["blinded_assessment_flag"] is True

def test_extract_unblinded():
    """Test extraction of unblinded study."""
    study = {
        "id": "test-unblinded",
        "rater_type": "unblinded",
        "blinded_assessment_flag": False
    }
    result = extract_blinding_status(study)
    assert result["rater_type"] == "unblinded"
    assert result["blinded_assessment_flag"] is False

def test_extract_mixed():
    """Test extraction of mixed blinding status."""
    study = {
        "id": "test-mixed",
        "rater_type": "mixed",
        "blinded_assessment_flag": True
    }
    result = extract_blinding_status(study)
    assert result["rater_type"] == "mixed"
    assert result["blinded_assessment_flag"] is True

def test_extract_missing_fields():
    """Test extraction when fields are missing."""
    study = {
        "id": "test-missing"
    }
    result = extract_blinding_status(study)
    assert result["rater_type"] == "unknown"
    assert result["blinded_assessment_flag"] is False
