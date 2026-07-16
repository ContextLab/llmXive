import json
import pytest
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def test_dataset_metadata_schema():
    """
    Contract test to validate the dataset metadata schema.
    
    Verifies that the metadata file contains all required fields
    with correct data types and structure.
    """
    metadata_path = project_root / "data" / "raw" / "dataset_metadata.json"
    
    # Skip test if metadata file doesn't exist yet
    if not metadata_path.exists():
        pytest.skip("Metadata file not found - download task may not have run yet")
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    # Validate top-level structure
    assert "dataset_name" in metadata, "Missing dataset_name"
    assert "created_at" in metadata, "Missing created_at"
    assert "source" in metadata, "Missing source"
    assert "measurement_conditions" in metadata, "Missing measurement_conditions"
    assert "data_quality" in metadata, "Missing data_quality"
    assert "schema" in metadata, "Missing schema"
    
    # Validate source section
    source = metadata["source"]
    assert "name" in source, "Missing source.name"
    assert "type" in source, "Missing source.type"
    assert "access_method" in source, "Missing source.access_method"
    assert "confidence_score" in source, "Missing source.confidence_score"
    
    # Validate confidence score is a number between 0 and 1
    assert 0 <= source["confidence_score"] <= 1, "confidence_score must be between 0 and 1"
    
    # Validate measurement conditions
    conditions = metadata["measurement_conditions"]
    assert isinstance(conditions, dict), "measurement_conditions must be a dictionary"
    
    # At least one condition should be specified
    assert len(conditions) > 0, "measurement_conditions should not be empty"
    
    # Validate data quality section
    quality = metadata["data_quality"]
    assert "filtering_applied" in quality, "Missing data_quality.filtering_applied"
    assert isinstance(quality["filtering_applied"], bool), "filtering_applied must be boolean"
    
    # Validate schema section
    schema = metadata["schema"]
    assert "required_fields" in schema, "Missing schema.required_fields"
    assert "optional_fields" in schema, "Missing schema.optional_fields"
    assert isinstance(schema["required_fields"], list), "required_fields must be a list"
    assert isinstance(schema["optional_fields"], list), "optional_fields must be a list"
    
    # Validate required fields contain expected columns
    expected_required = ["smiles"]
    for field in expected_required:
        assert field in schema["required_fields"], f"Missing required field: {field}"

def test_metadata_experimental_source():
    """
    Test that metadata explicitly documents the experimental source.
    """
    metadata_path = project_root / "data" / "raw" / "dataset_metadata.json"
    
    if not metadata_path.exists():
        pytest.skip("Metadata file not found")
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    # Check that source name is explicitly documented
    source_name = metadata["source"]["name"]
    assert source_name in ["ChEMBL", "MoleculeNet"], f"Unexpected source: {source_name}"
    
    # Check that access method is documented
    access_method = metadata["source"]["access_method"]
    assert "huggingface" in access_method.lower(), "Access method should reference HuggingFace"

def test_metadata_measurement_conditions():
    """
    Test that measurement conditions are documented.
    """
    metadata_path = project_root / "data" / "raw" / "dataset_metadata.json"
    
    if not metadata_path.exists():
        pytest.skip("Metadata file not found")
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    conditions = metadata["measurement_conditions"]
    
    # Should have at least temperature or pH mentioned
    has_temp = any("temperature" in k.lower() for k in conditions.keys())
    has_ph = any("ph" in k.lower() for k in conditions.keys())
    has_pressure = any("pressure" in k.lower() for k in conditions.keys())
    
    assert has_temp or has_ph or has_pressure, \
        "Measurement conditions should include temperature, pH, or pressure"

def test_metadata_confidence_score():
    """
    Test that source confidence is documented as a numeric value.
    """
    metadata_path = project_root / "data" / "raw" / "dataset_metadata.json"
    
    if not metadata_path.exists():
        pytest.skip("Metadata file not found")
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    confidence = metadata["source"]["confidence_score"]
    assert isinstance(confidence, (int, float)), "confidence_score must be numeric"
    assert 0 <= confidence <= 1, "confidence_score must be between 0 and 1"
    
    # Should be reasonably high for experimental data
    assert confidence >= 0.5, "Confidence score should be at least 0.5 for experimental data"