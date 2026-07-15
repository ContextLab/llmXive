import json
import os
import tempfile
from pathlib import Path
import pytest
import yaml
import jsonschema

# Import the validator module
from code.dataset_config_validator import load_schema, validate_config, create_sample_config

# Path constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset-config.schema.yaml"
CONFIG_PATH = PROJECT_ROOT / "data" / "config" / "dataset_ids.json"

@pytest.fixture
def valid_schema():
    """Load the valid schema for testing."""
    if not SCHEMA_PATH.exists():
        pytest.skip(f"Schema file not found at {SCHEMA_PATH}")
    return load_schema(str(SCHEMA_PATH))

@pytest.fixture
def valid_config():
    """Load a valid configuration for testing."""
    if not CONFIG_PATH.exists():
        pytest.skip(f"Config file not found at {CONFIG_PATH}")
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    sample_data = {
        "version": "1.0.0",
        "description": "Test configuration",
        "datasets": [
            {
                "id": "TEST001",
                "source": "ncbi_sra",
                "description": "Test dataset",
                "metadata": {
                    "wetland_type": "constructed",
                    "nutrient_removal": True,
                    "target_nutrients": ["nitrogen"],
                    "sampling_stages": ["early"],
                    "location": "Test Location",
                    "study_period": "12_months"
                }
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_data, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)

@pytest.fixture
def temp_schema_file():
    """Create a temporary schema file for testing."""
    with open(SCHEMA_PATH, 'r') as f:
        schema_content = f.read()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(schema_content)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)

class TestDatasetConfigSchema:
    """Contract tests for dataset configuration schema validation."""

    def test_schema_loads_successfully(self, valid_schema):
        """Test that the schema can be loaded without errors."""
        assert valid_schema is not None
        assert valid_schema.get('type') == 'object'
        assert 'required' in valid_schema
        assert 'properties' in valid_schema

    def test_valid_config_passes_validation(self, valid_config, temp_schema_file):
        """Test that a valid configuration passes validation."""
        # Create a temp config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(valid_config, f)
            temp_config_path = f.name
        
        try:
            is_valid, errors = validate_config(temp_config_path, temp_schema_file)
            assert is_valid, f"Validation failed with errors: {errors}"
            assert len(errors) == 0
        finally:
            if os.path.exists(temp_config_path):
                os.unlink(temp_config_path)

    def test_invalid_version_format(self, temp_config_file, temp_schema_file):
        """Test that invalid version format is caught."""
        # Load and modify the temp config
        with open(temp_config_file, 'r') as f:
            config = json.load(f)
        
        config['version'] = 'invalid-version'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            temp_path = f.name
        
        try:
            is_valid, errors = validate_config(temp_path, temp_schema_file)
            assert not is_valid
            assert any('version' in error.lower() for error in errors)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_missing_required_field(self, temp_config_file, temp_schema_file):
        """Test that missing required fields are caught."""
        with open(temp_config_file, 'r') as f:
            config = json.load(f)
        
        # Remove a required field
        del config['description']
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            temp_path = f.name
        
        try:
            is_valid, errors = validate_config(temp_path, temp_schema_file)
            assert not is_valid
            assert any('description' in error.lower() for error in errors)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_invalid_source_enum(self, temp_config_file, temp_schema_file):
        """Test that invalid source values are caught."""
        with open(temp_config_file, 'r') as f:
            config = json.load(f)
        
        config['datasets'][0]['source'] = 'invalid_source'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            temp_path = f.name
        
        try:
            is_valid, errors = validate_config(temp_path, temp_schema_file)
            assert not is_valid
            assert any('source' in error.lower() for error in errors)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_empty_datasets_array(self, temp_config_file, temp_schema_file):
        """Test that empty datasets array is caught."""
        with open(temp_config_file, 'r') as f:
            config = json.load(f)
        
        config['datasets'] = []
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            temp_path = f.name
        
        try:
            is_valid, errors = validate_config(temp_path, temp_schema_file)
            assert not is_valid
            assert any('datasets' in error.lower() or 'array' in error.lower() for error in errors)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_create_sample_config(self):
        """Test that create_sample_config generates a valid file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            sample_path = f.name
        
        try:
            create_sample_config(sample_path)
            
            assert os.path.exists(sample_path)
            
            with open(sample_path, 'r') as f:
                config = json.load(f)
            
            # Validate the generated config
            is_valid, errors = validate_config(sample_path, str(SCHEMA_PATH))
            assert is_valid, f"Generated sample config is invalid: {errors}"
        finally:
            if os.path.exists(sample_path):
                os.unlink(sample_path)

    def test_file_not_found_handling(self, temp_schema_file):
        """Test that missing config file is handled gracefully."""
        is_valid, errors = validate_config("/nonexistent/path/config.json", temp_schema_file)
        assert not is_valid
        assert any("not found" in error.lower() for error in errors)

    def test_schema_not_found_handling(self, temp_config_file):
        """Test that missing schema file is handled gracefully."""
        is_valid, errors = validate_config(temp_config_file, "/nonexistent/path/schema.yaml")
        assert not is_valid
        assert any("not found" in error.lower() for error in errors)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
