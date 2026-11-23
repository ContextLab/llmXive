import json
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import os

# Import the functions we want to test
# We'll mock the imports from 01_download_and_score and utils.schema_validator
# since we are testing the logic in isolation

def create_mock_dataframe():
    """Create a mock dataframe for testing."""
    data = {
        "quality_rating": [1, 2, 3, 4, 5] * 40,  # 200 rows
        "user_id": [f"user_{i}" for i in range(200)],
        "dialogue_id": [f"dialogue_{i}" for i in range(200)],
        "age": ["18-25"] * 100 + ["26-35"] * 60 + ["36-45"] * 40,
        "gender": ["Male"] * 110 + ["Female"] * 90
    }
    return pd.DataFrame(data)

def create_small_dataframe():
    """Create a small dataframe that fails the total sample size check."""
    data = {
        "quality_rating": [1, 2, 3] * 10,  # 30 rows
        "user_id": [f"user_{i}" for i in range(30)],
        "dialogue_id": [f"dialogue_{i}" for i in range(30)],
        "age": ["18-25"] * 30,
        "gender": ["Male"] * 30
    }
    return pd.DataFrame(data)

def create_dataframe_missing_fields():
    """Create a dataframe missing required fields."""
    data = {
        "user_id": [f"user_{i}" for i in range(100)],
        "dialogue_id": [f"dialogue_{i}" for i in range(100)],
        "age": ["18-25"] * 100,
        "gender": ["Male"] * 100
        # Missing quality_rating
    }
    return pd.DataFrame(data)

def create_dataframe_missing_demographics():
    """Create a dataframe missing demographic fields."""
    data = {
        "quality_rating": [1, 2, 3] * 40,
        "user_id": [f"user_{i}" for i in range(120)],
        "dialogue_id": [f"dialogue_{i}" for i in range(120)]
        # Missing age and gender
    }
    return pd.DataFrame(data)

def create_dataframe_small_subgroups():
    """Create a dataframe with small subgroups."""
    data = {
        "quality_rating": [1, 2, 3] * 40,
        "user_id": [f"user_{i}" for i in range(120)],
        "dialogue_id": [f"dialogue_{i}" for i in range(120)],
        "age": ["18-25"] * 40 + ["26-35"] * 30 + ["36-45"] * 50,
        "gender": ["Male"] * 60 + ["Female"] * 60
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_validate_sample_size():
    """Fixture to import the function dynamically."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "verify_sample_size", 
        "code/01_verify_sample_size.py"
    )
    module = importlib.util.module_from_spec(spec)
    # Mock the imports that might fail
    import sys
    sys.modules['01_download_and_score'] = type(sys)('01_download_and_score')
    sys.modules['01_download_and_score'].load_dataset_with_check = lambda x: None
    sys.modules['utils'] = type(sys)('utils')
    sys.modules['utils.schema_validator'] = type(sys)('utils.schema_validator')
    sys.modules['utils.schema_validator'].get_missing_fields = lambda x: []
    sys.modules['utils.schema_validator'].load_schema = lambda x: {}
    
    spec.loader.exec_module(module)
    return module.validate_sample_size

def test_total_sample_size_valid(mock_validate_sample_size):
    """Test that a dataframe with sufficient total sample size passes."""
    df = create_mock_dataframe()
    report = mock_validate_sample_size(df)
    
    assert report["total_sample_size"] == 200
    assert report["primary_analysis_valid"] is True
    assert report["status"] in ["full", "partial"]

def test_total_sample_size_insufficient(mock_validate_sample_size):
    """Test that a dataframe with insufficient total sample size fails."""
    df = create_small_dataframe()
    report = mock_validate_sample_size(df)
    
    assert report["total_sample_size"] == 30
    assert report["primary_analysis_valid"] is False
    assert report["status"] == "missing"

def test_missing_required_fields(mock_validate_sample_size):
    """Test that missing required fields are detected."""
    df = create_dataframe_missing_fields()
    report = mock_validate_sample_size(df)
    
    assert "quality_rating" in report["missing_fields"]
    assert report["primary_analysis_valid"] is False

def test_missing_demographics(mock_validate_sample_size):
    """Test that missing demographic fields are handled."""
    df = create_dataframe_missing_demographics()
    report = mock_validate_sample_size(df)
    
    # Should have age and gender in missing fields
    assert "age" in report["missing_fields"]
    assert "gender" in report["missing_fields"]
    # Primary analysis can still be valid if core fields are present
    assert report["primary_analysis_valid"] is True
    assert report["status"] == "missing_demographics"

def test_subgroup_eligibility(mock_validate_sample_size):
    """Test that subgroups with n >= 30 are eligible."""
    df = create_mock_dataframe()
    report = mock_validate_sample_size(df)
    
    # Check that some subgroups are eligible
    assert len(report["subgroups_eligible"]) > 0
    # Check that no subgroups are excluded (all should be >= 30)
    assert len(report["subgroups_excluded"]) == 0

def test_subgroup_exclusion(mock_validate_sample_size):
    """Test that subgroups with n < 30 are excluded."""
    df = create_dataframe_small_subgroups()
    report = mock_validate_sample_size(df)
    
    # Check that some subgroups are excluded
    assert len(report["subgroups_excluded"]) > 0
    # Check that some subgroups are still eligible
    assert len(report["subgroups_eligible"]) > 0

def test_report_structure(mock_validate_sample_size):
    """Test that the report has the correct structure."""
    df = create_mock_dataframe()
    report = mock_validate_sample_size(df)
    
    required_keys = [
        "status", "total_sample_size", "primary_analysis_valid",
        "missing_fields", "subgroup_counts", "subgroups_eligible", "subgroups_excluded"
    ]
    
    for key in required_keys:
        assert key in report, f"Missing key in report: {key}"
    
    assert isinstance(report["subgroup_counts"], dict)
    assert isinstance(report["subgroups_eligible"], list)
    assert isinstance(report["subgroups_excluded"], list)
