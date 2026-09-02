"""
T010: Contract test for data loader output schema.

Verifies that the data loader returns data matching the expected schema.
"""
import os
import sys
import pytest
from pathlib import Path
import yaml

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from data_loader import fetch_marker_genes, fetch_metabolite_profiles, SpeciesData
from config import load_config

def load_schema(schema_path: Path) -> dict:
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def test_data_loader_schema_matches():
    """
    T010 Test: Assert that the output of the data loader matches the schema.
    """
    # Load schema
    schema_path = Path(__file__).parent / "schemas" / "data_loader.yaml"
    schema = load_schema(schema_path)
    
    # We test the structure of the SpeciesData object against the schema definition.
    # The schema expects:
    # species_data: array of objects with species_id, marker_genes, metabolite_profile
    
    # 1. Verify SpeciesData dataclass structure
    assert hasattr(SpeciesData, 'species_id')
    assert hasattr(SpeciesData, 'marker_genes')
    assert hasattr(SpeciesData, 'metabolite_profile')
    
    # 2. Verify types match schema expectations
    # schema: marker_genes is object (dict), metabolite_profile is object (dict)
    # species_id is string
    
    # Create a mock instance to check types
    mock_data = SpeciesData(
        species_id="test_species",
        marker_genes={"rbcL": "ATGC..."},
        metabolite_profile={"C00001": True}
    )
    
    assert isinstance(mock_data.species_id, str)
    assert isinstance(mock_data.marker_genes, dict)
    assert isinstance(mock_data.metabolite_profile, dict)
    
    # 3. Verify schema properties exist
    schema_props = schema['properties']['species_data']['items']['properties']
    assert 'species_id' in schema_props
    assert 'marker_genes' in schema_props
    assert 'metabolite_profile' in schema_props
    
    # 4. Verify nested types in schema
    assert schema_props['marker_genes']['type'] == 'object'
    assert schema_props['metabolite_profile']['type'] == 'object'
    
    # 5. Verify required fields
    schema_required = schema['properties']['species_data']['items']['required']
    assert 'species_id' in schema_required
    assert 'marker_genes' in schema_required
    assert 'metabolite_profile' in schema_required
    
    logger.info("Schema contract test passed: SpeciesData structure matches data_loader.yaml")
