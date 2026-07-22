"""
Unit tests for code/data/validate.py
"""
import pytest
import sys
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
from code.data.validate import validate_metadata, FatalError, run_validation
from code.config import Config

# Set up logging to avoid errors during tests
logging.basicConfig(level=logging.INFO)

def test_validate_metadata_with_required_fields():
    """Test validation passes when required fields are present"""
    config = Config()
    # Ensure config has required variables
    config.REQUIRED_VARIABLES = ["pre_treatment_score", "post_treatment_score"]
    
    metadata = {
        "variables": ["pre_treatment_score", "post_treatment_score"],
        "instrument": "GAD-7"
    }
    
    # Should not raise an error
    is_valid, errors = validate_metadata(metadata, config)
    assert is_valid is True
    assert len(errors) == 0

def test_validate_metadata_missing_pre_score():
    """Test validation fails when pre_treatment_score is missing"""
    config = Config()
    config.REQUIRED_VARIABLES = ["pre_treatment_score", "post_treatment_score"]
    
    metadata = {
        "variables": ["post_treatment_score"],
        "instrument": "GAD-7"
    }
    
    # Should raise FatalError
    with pytest.raises(FatalError, match="Missing required variable: pre_treatment_score"):
        validate_metadata(metadata, config)

def test_validate_metadata_missing_post_score():
    """Test validation fails when post_treatment_score is missing"""
    config = Config()
    config.REQUIRED_VARIABLES = ["pre_treatment_score", "post_treatment_score"]
    
    metadata = {
        "variables": ["pre_treatment_score"],
        "instrument": "GAD-7"
    }
    
    # Should raise FatalError
    with pytest.raises(FatalError, match="Missing required variable: post_treatment_score"):
        validate_metadata(metadata, config)

def test_validate_metadata_invalid_instrument():
    """Test validation fails when instrument is not validated"""
    config = Config()
    config.REQUIRED_VARIABLES = ["pre_treatment_score", "post_treatment_score"]
    
    metadata = {
        "variables": ["pre_treatment_score", "post_treatment_score"],
        "instrument": "InvalidScale"
    }
    
    # Should raise FatalError
    with pytest.raises(FatalError, match="Invalid instrument"):
        validate_metadata(metadata, config)

def test_run_validation_fails_on_missing_verified_source():
    """Test run_validation raises FatalError if verified sources file is missing"""
    config = Config()
    config.VERIFIED_SOURCES_PATH = Path("/nonexistent/verified_sources.json")
    
    with pytest.raises(FatalError, match="Missing verified dataset source"):
        run_validation(config)

def test_run_validation_fails_on_invalid_json():
    """Test run_validation raises FatalError if verified sources file is invalid JSON"""
    config = Config()
    # Create a temporary file with invalid JSON
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        f.write("not valid json")
        temp_path = Path(f.name)
    
    try:
        config.VERIFIED_SOURCES_PATH = temp_path
        with pytest.raises(FatalError, match="Invalid verified sources file"):
            run_validation(config)
    finally:
        temp_path.unlink()

def test_run_validation_fails_on_missing_raw_data_dir():
    """Test run_validation raises FatalError if raw data directory is missing"""
    config = Config()
    config.REQUIRED_VARIABLES = ["pre_treatment_score", "post_treatment_score"]
    
    # Mock verified sources to exist and be valid
    import tempfile
    import json
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump({"openneuro_id": "ds-test"}, f)
        temp_path = Path(f.name)
    
    try:
        config.VERIFIED_SOURCES_PATH = temp_path
        config.RAW_DATA_DIR = Path("/nonexistent/raw_data")
        
        with pytest.raises(FatalError, match="Raw data directory not found"):
            run_validation(config)
    finally:
        temp_path.unlink()
