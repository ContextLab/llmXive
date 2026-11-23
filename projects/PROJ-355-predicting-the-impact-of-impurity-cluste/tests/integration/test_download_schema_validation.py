import pytest
import yaml
import json
from pathlib import Path
import tempfile
import os
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.download import validate_dataset
from jsonschema import ValidationError

@pytest.mark.integration
def test_full_validation_workflow():
    """Integration test: Validate a realistic dataset against the project schema."""
    # Load the actual project schema
    project_root = Path(__file__).parent.parent.parent.parent / 'projects' / 'PROJ-355-predicting-the-impact-of-impurity-cluste'
    schema_path = project_root / 'contracts' / 'dataset.schema.yaml'
    
    if not schema_path.exists():
        pytest.skip(f"Schema file not found at {schema_path}")
    
    # Create a realistic valid dataset
    valid_dataset = {
        "bulk_config_id": "mp-12345",
        "impurity_species": "Cr",
        "alloy_system_id": "BCC_Cr",
        "clustering_descriptors": {
            "rdf_peak": 2.45,
            "pair_corr": 0.82,
            "voronoi_count": 12
        },
        "segregation_energy": -0.45
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(valid_dataset, f)
        data_path = Path(f.name)
    
    try:
        # This should pass without raising
        result = validate_dataset(data_path, schema_path)
        assert result is True
    finally:
        os.unlink(data_path)

@pytest.mark.integration
def test_validation_catches_missing_fields():
    """Integration test: Validation catches missing required fields."""
    project_root = Path(__file__).parent.parent.parent.parent / 'projects' / 'PROJ-355-predicting-the-impact-of-impurity-cluste'
    schema_path = project_root / 'contracts' / 'dataset.schema.yaml'
    
    if not schema_path.exists():
        pytest.skip(f"Schema file not found at {schema_path}")
    
    # Dataset missing required 'impurity_species'
    invalid_dataset = {
        "bulk_config_id": "mp-12345",
        "alloy_system_id": "BCC_Cr",
        "clustering_descriptors": {
            "rdf_peak": 2.45,
            "pair_corr": 0.82,
            "voronoi_count": 12
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(invalid_dataset, f)
        data_path = Path(f.name)
    
    try:
        with pytest.raises(ValidationError):
            validate_dataset(data_path, schema_path)
    finally:
        os.unlink(data_path)

@pytest.mark.integration
def test_validation_catches_wrong_types():
    """Integration test: Validation catches type mismatches."""
    project_root = Path(__file__).parent.parent.parent.parent / 'projects' / 'PROJ-355-predicting-the-impact-of-impurity-cluste'
    schema_path = project_root / 'contracts' / 'dataset.schema.yaml'
    
    if not schema_path.exists():
        pytest.skip(f"Schema file not found at {schema_path}")
    
    # Dataset with wrong type (string instead of number for rdf_peak)
    invalid_dataset = {
        "bulk_config_id": "mp-12345",
        "impurity_species": "Cr",
        "alloy_system_id": "BCC_Cr",
        "clustering_descriptors": {
            "rdf_peak": "not_a_number",
            "pair_corr": 0.82,
            "voronoi_count": 12
        },
        "segregation_energy": -0.45
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(invalid_dataset, f)
        data_path = Path(f.name)
    
    try:
        with pytest.raises(ValidationError):
            validate_dataset(data_path, schema_path)
    finally:
        os.unlink(data_path)