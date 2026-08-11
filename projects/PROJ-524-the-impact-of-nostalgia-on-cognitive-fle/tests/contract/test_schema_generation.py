"""
Contract tests for Schema Generation (Task T020a).
Validates that the generated schema files contain the required fields.
"""

import os
import yaml
import pytest
from pathlib import Path

# Test constants
REQUIRED_DATASET_FIELDS = [
    'participant_id',
    'age',
    'stimulus_type',
    'perseverative_errors',
    'categories_completed',
    'MMSE'  # Optional but must be defined
]

REQUIRED_OUTPUT_SECTIONS = [
    'analysis_metadata',
    'group_statistics',
    'hypothesis_tests',
    'effect_sizes',
    'power_analysis'
]

@pytest.fixture
def contracts_dir():
    """Get the contracts directory path."""
    return Path('contracts')

@pytest.fixture
def dataset_schema_path(contracts_dir):
    """Get the dataset schema file path."""
    return contracts_dir / 'dataset.schema.yaml'

@pytest.fixture
def output_schema_path(contracts_dir):
    """Get the output schema file path."""
    return contracts_dir / 'output.schema.yaml'

@pytest.fixture
def dataset_schema(dataset_schema_path):
    """Load the dataset schema."""
    if not dataset_schema_path.exists():
        pytest.skip(f"Dataset schema file not found at {dataset_schema_path}")
    with open(dataset_schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

@pytest.fixture
def output_schema(output_schema_path):
    """Load the output schema."""
    if not output_schema_path.exists():
        pytest.skip(f"Output schema file not found at {output_schema_path}")
    with open(output_schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

class TestDatasetSchema:
    """Tests for the dataset schema."""
    
    def test_schema_file_exists(self, dataset_schema_path):
        """Test that the dataset schema file exists."""
        assert dataset_schema_path.exists(), f"Dataset schema file not found: {dataset_schema_path}"
    
    def test_schema_is_valid_yaml(self, dataset_schema):
        """Test that the schema is valid YAML."""
        assert dataset_schema is not None
        assert isinstance(dataset_schema, dict)
    
    def test_schema_has_title(self, dataset_schema):
        """Test that the schema has a title."""
        assert 'title' in dataset_schema
        assert 'WCST' in dataset_schema['title'] or 'Dataset' in dataset_schema['title']
    
    def test_required_fields_present(self, dataset_schema):
        """Test that all required fields are defined in properties."""
        properties = dataset_schema.get('properties', {})
        required_fields = REQUIRED_DATASET_FIELDS
        
        for field in required_fields:
            assert field in properties, f"Required field '{field}' not found in schema properties"
    
    def test_participant_id_field(self, dataset_schema):
        """Test the participant_id field definition."""
        properties = dataset_schema.get('properties', {})
        participant_id = properties.get('participant_id', {})
        
        assert participant_id.get('type') == 'string'
        assert 'description' in participant_id
    
    def test_age_field(self, dataset_schema):
        """Test the age field definition."""
        properties = dataset_schema.get('properties', {})
        age = properties.get('age', {})
        
        assert age.get('type') == 'integer'
        assert age.get('minimum') == 65
    
    def test_stimulus_type_field(self, dataset_schema):
        """Test the stimulus_type field definition."""
        properties = dataset_schema.get('properties', {})
        stimulus_type = properties.get('stimulus_type', {})
        
        assert stimulus_type.get('type') == 'string'
        enum_values = stimulus_type.get('enum', [])
        assert 'nostalgia' in enum_values
        assert 'control' in enum_values
    
    def test_perseverative_errors_field(self, dataset_schema):
        """Test the perseverative_errors field definition."""
        properties = dataset_schema.get('properties', {})
        pe = properties.get('perseverative_errors', {})
        
        assert pe.get('type') == 'integer'
        assert pe.get('minimum') == 0
    
    def test_categories_completed_field(self, dataset_schema):
        """Test the categories_completed field definition."""
        properties = dataset_schema.get('properties', {})
        cc = properties.get('categories_completed', {})
        
        assert cc.get('type') == 'integer'
        assert cc.get('minimum') == 0
    
    def test_mmse_field_optional(self, dataset_schema):
        """Test that MMSE field is defined and optional."""
        properties = dataset_schema.get('properties', {})
        mmse = properties.get('MMSE', {})
        
        assert mmse.get('type') == 'integer'
        assert mmse.get('nullable') is True
    
    def test_required_list_includes_core_fields(self, dataset_schema):
        """Test that the required list includes core fields."""
        required = dataset_schema.get('required', [])
        core_fields = ['participant_id', 'age', 'stimulus_type', 'perseverative_errors', 'categories_completed']
        
        for field in core_fields:
            assert field in required, f"Core field '{field}' not in required list"

class TestOutputSchema:
    """Tests for the output schema."""
    
    def test_schema_file_exists(self, output_schema_path):
        """Test that the output schema file exists."""
        assert output_schema_path.exists(), f"Output schema file not found at {output_schema_path}"
    
    def test_schema_is_valid_yaml(self, output_schema):
        """Test that the schema is valid YAML."""
        assert output_schema is not None
        assert isinstance(output_schema, dict)
    
    def test_schema_has_title(self, output_schema):
        """Test that the schema has a title."""
        assert 'title' in output_schema
        assert 'Analysis' in output_schema['title'] or 'Output' in output_schema['title']
    
    def test_required_sections_present(self, output_schema):
        """Test that all required sections are defined."""
        required_sections = REQUIRED_OUTPUT_SECTIONS
        properties = output_schema.get('properties', {})
        
        for section in required_sections:
            assert section in properties, f"Required section '{section}' not found in output schema"
    
    def test_hypothesis_tests_structure(self, output_schema):
        """Test the hypothesis_tests structure."""
        hypothesis_tests = output_schema.get('properties', {}).get('hypothesis_tests', {}).get('properties', {})
        
        assert 'perseverative_errors' in hypothesis_tests
        assert 'categories_completed' in hypothesis_tests
        
        # Check for Welch's t-test specific fields
        pe_test = hypothesis_tests.get('perseverative_errors', {}).get('properties', {})
        assert 't_statistic' in pe_test
        assert 'p_value' in pe_test
        assert 'degrees_of_freedom' in pe_test
        assert 'method' in pe_test
    
    def test_effect_sizes_structure(self, output_schema):
        """Test the effect_sizes structure."""
        effect_sizes = output_schema.get('properties', {}).get('effect_sizes', {}).get('properties', {})
        
        assert 'perseverative_errors' in effect_sizes
        assert 'categories_completed' in effect_sizes
        
        # Check for Cohen's d fields
        pe_effect = effect_sizes.get('perseverative_errors', {}).get('properties', {})
        assert 'cohen_d' in pe_effect
        assert 'ci_lower' in pe_effect
        assert 'ci_upper' in pe_effect
    
    def test_power_analysis_structure(self, output_schema):
        """Test the power_analysis structure."""
        power_analysis = output_schema.get('properties', {}).get('power_analysis', {}).get('properties', {})
        
        assert 'achieved_power' in power_analysis
        assert 'minimum_detectable_effect' in power_analysis
    
    def test_sensitivity_analysis_structure(self, output_schema):
        """Test the sensitivity_analysis structure."""
        sensitivity = output_schema.get('properties', {}).get('sensitivity_analysis', {}).get('properties', {})
        
        assert 'threshold_sweep' in sensitivity
        assert 'borderline_status' in sensitivity
        
        # Check for borderline flag
        borderline = sensitivity.get('borderline_status', {}).get('properties', {})
        assert 'is_sensitive_to_threshold' in borderline