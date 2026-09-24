"""
Integration test for data contract validation.

This test verifies that the dataset schema validation works correctly
with real (or mock) data structures that should pass validation.
"""
import pytest
import yaml
from pathlib import Path
from validators import validate_schema


def test_dataset_schema_validation(tmp_path):
    """Test that valid dataset entries pass schema validation."""
    # Load the actual schema from the project
    root = Path(__file__).parent.parent.parent
    schema_path = root / "contracts" / "dataset.schema.yaml"
    
    assert schema_path.exists(), "Dataset schema file not found"
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    # Create a valid dataset entry based on the schema
    valid_entry = {
        "bulk_config_id": "mp-12345",
        "impurity_species": "Cr",
        "alloy_system_id": "BCC_Cr",
        "clustering_descriptors": {
            "rdf_peak": 2.85,
            "pair_corr": 0.42,
            "voronoi_count": 12
        },
        "segregation_energy": -0.15
    }
    
    # Validate the entry
    result = validate_schema(valid_entry, str(schema_path))
    assert result is True, "Valid entry failed schema validation"

def test_dataset_schema_rejects_invalid(tmp_path):
    """Test that invalid dataset entries fail schema validation."""
    root = Path(__file__).parent.parent.parent
    schema_path = root / "contracts" / "dataset.schema.yaml"
    
    # Create an invalid entry (missing required field)
    invalid_entry = {
        "bulk_config_id": "mp-12345",
        # Missing impurity_species, alloy_system_id, etc.
    }
    
    with pytest.raises(Exception):
        validate_schema(invalid_entry, str(schema_path))
