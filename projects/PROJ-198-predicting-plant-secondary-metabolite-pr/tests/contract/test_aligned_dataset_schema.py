"""
Contract test for the Aligned Dataset schema.
Validates that data structures conform to the JSON schema defined in contracts/.
"""
import pytest
import json
import yaml
from pathlib import Path

# Import schema validator
try:
    from jsonschema import validate, ValidationError
except ImportError:
    pytest.skip("jsonschema not installed", allow_module_level=True)

@pytest.fixture
def aligned_dataset_schema():
    """Load the aligned dataset schema."""
    schema_path = Path(__file__).parent.parent.parent / "contracts" / "aligned_dataset.schema.yaml"
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def test_valid_aligned_dataset(sample_aligned_data, aligned_dataset_schema):
    """Test that valid aligned data passes schema validation."""
    try:
        validate(instance=sample_aligned_data, schema=aligned_dataset_schema)
    except ValidationError as e:
        pytest.fail(f"Valid data failed schema validation: {e.message}")

def test_missing_species_id(sample_aligned_data, aligned_dataset_schema):
    """Test that missing required field 'species_id' fails validation."""
    invalid_data = sample_aligned_data.copy()
    del invalid_data["species_id"]
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=aligned_dataset_schema)

def test_invalid_bgc_count_type(sample_aligned_data, aligned_dataset_schema):
    """Test that non-integer BGC count fails validation."""
    invalid_data = sample_aligned_data.copy()
    invalid_data["bgc_counts"] = {"NRPS": "ten"}  # Should be integer
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=aligned_dataset_schema)

def test_negative_bgc_count(sample_aligned_data, aligned_dataset_schema):
    """Test that negative BGC count fails validation."""
    invalid_data = sample_aligned_data.copy()
    invalid_data["bgc_counts"] = {"NRPS": -5}
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=aligned_dataset_schema)

def test_invalid_metabolite_abundance_type(sample_aligned_data, aligned_dataset_schema):
    """Test that non-numeric metabolite abundance fails validation."""
    invalid_data = sample_aligned_data.copy()
    invalid_data["metabolite_abundances"] = {"InChIKey1": "high"}
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=aligned_dataset_schema)
