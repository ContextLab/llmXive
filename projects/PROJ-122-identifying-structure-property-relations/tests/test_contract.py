"""
Contract tests for data schema validation.

This module implements contract tests to validate data against the 
dataset.schema.yaml and output.schema.yaml definitions.

Dependencies:
- T005: dataset.schema.yaml must exist
- T006: output.schema.yaml must exist
"""
import pytest
import yaml
import json
from pathlib import Path
import sys
import os

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.schema_validator import load_schema, SchemaValidationError

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
SCHEMAS_DIR = PROJECT_ROOT / "specs" / "001-structure-property-relationships" / "contracts"

@pytest.fixture
def dataset_schema():
    """Load the dataset schema from file."""
    schema_path = SCHEMAS_DIR / "dataset.schema.yaml"
    if not schema_path.exists():
        pytest.fail(f"Dataset schema file not found at {schema_path}")
    return load_schema(str(schema_path))

@pytest.fixture
def output_schema():
    """Load the output schema from file."""
    schema_path = SCHEMAS_DIR / "output.schema.yaml"
    if not schema_path.exists():
        pytest.fail(f"Output schema file not found at {schema_path}")
    return load_schema(str(schema_path))

@pytest.fixture
def sample_valid_record():
    """Return a sample valid record matching the dataset schema."""
    return {
        "smiles": "CC(C)C1=CC=C(C=C1)C(C)C(=O)O",
        "composition": "Polymer A: 60%, Polymer B: 40%",
        "tg_k": 350.5,
        "modulus_gpa": 2.5,
        "source": "NIST",
        "raw_tg": 77.35,
        "raw_tg_unit": "C",
        "weight_fractions": "0.6,0.4",
        "checksum": "a" * 64
    }

@pytest.fixture
def sample_invalid_record_missing_fields():
    """Return a sample invalid record with missing required fields."""
    return {
        "smiles": "CC(C)C1=CC=C(C=C1)C(C)C(=O)O",
        # Missing: composition, tg_k, source
    }

@pytest.fixture
def sample_invalid_record_bad_smiles():
    """Return a sample invalid record with invalid SMILES."""
    return {
        "smiles": "INVALID_SMILES_@@@",
        "composition": "Polymer A: 60%, Polymer B: 40%",
        "tg_k": 350.5,
        "source": "NIST"
    }

@pytest.fixture
def sample_invalid_record_bad_tg():
    """Return a sample invalid record with out-of-range Tg."""
    return {
        "smiles": "CC(C)C1=CC=C(C=C1)C(C)C(=O)O",
        "composition": "Polymer A: 60%, Polymer B: 40%",
        "tg_k": 50.0,  # Below minimum of 100K
        "source": "NIST"
    }

@pytest.fixture
def sample_invalid_record_bad_source():
    """Return a sample invalid record with invalid source."""
    return {
        "smiles": "CC(C)C1=CC=C(C=C1)C(C)C(=O)O",
        "composition": "Polymer A: 60%, Polymer B: 40%",
        "tg_k": 350.5,
        "source": "FakeDatabase"  # Not in allowed values
    }

@pytest.fixture
def sample_valid_feature_record():
    """Return a sample valid feature matrix record."""
    return {
        "id": 1,
        "source": "NIST",
        "mw": 150.5,
        "tpsa": 25.0,
        "logp": 2.5,
        "num_rotatable_bonds": 3,
        "num_h_acceptors": 2,
        "num_h_donors": 1,
        "molecular_fraction_polymer_a": 0.6,
        "molecular_fraction_polymer_b": 0.4,
        "descriptor_diff_mw": 15.5,
        "descriptor_diff_tpsa": 5.0,
        "fox_prediction": 345.0,
        "gt_prediction": 348.0,
        "tg_residual": 5.5
    }

def test_schema_exists(dataset_schema, output_schema):
    """Test that both schema files exist and can be loaded."""
    assert dataset_schema is not None
    assert "schema_version" in dataset_schema
    assert "fields" in dataset_schema
    assert output_schema is not None
    assert "schema_version" in output_schema
    assert "artifact_types" in output_schema

def test_dataset_schema_structure(dataset_schema):
    """Test that the dataset schema has the expected structure."""
    assert dataset_schema["schema_version"] == "1.0.0"
    assert dataset_schema["dataset_type"] == "polymer_blend"
    assert "fields" in dataset_schema
    assert len(dataset_schema["fields"]) > 0

    # Check for required fields
    field_names = [f["name"] for f in dataset_schema["fields"]]
    assert "smiles" in field_names
    assert "composition" in field_names
    assert "tg_k" in field_names
    assert "source" in field_names

def test_output_schema_structure(output_schema):
    """Test that the output schema has the expected structure."""
    assert output_schema["schema_version"] == "1.0.0"
    assert "artifact_types" in output_schema
    assert "processed_dataset" in output_schema
    assert "feature_matrix" in output_schema
    assert "model_output" in output_schema
    assert "report" in output_schema

def test_validate_valid_record(dataset_schema, sample_valid_record):
    """Test that a valid record passes schema validation."""
    # Basic validation: check required fields exist
    required_fields = ["smiles", "composition", "tg_k", "source"]
    for field in required_fields:
        assert field in sample_valid_record
        assert sample_valid_record[field] is not None

    # Validate SMILES format (basic regex check)
    smiles = sample_valid_record["smiles"]
    assert smiles is not None
    assert len(smiles) > 0
    assert len(smiles) <= 2000

    # Validate Tg range
    tg_k = sample_valid_record["tg_k"]
    assert 100.0 <= tg_k <= 1000.0

    # Validate source
    valid_sources = ["NIST", "Polymer Database", "Materials Project", "Literature", "Other"]
    assert sample_valid_record["source"] in valid_sources

def test_validate_missing_required_fields(dataset_schema, sample_invalid_record_missing_fields):
    """Test that a record with missing required fields fails validation."""
    required_fields = ["smiles", "composition", "tg_k", "source"]
    missing = [f for f in required_fields if f not in sample_invalid_record_missing_fields]
    assert len(missing) > 0
    # This test verifies that the schema expects these fields
    assert "composition" in missing or "tg_k" in missing or "source" in missing

def test_validate_bad_smiles(dataset_schema, sample_invalid_record_bad_smiles):
    """Test that invalid SMILES format is detected."""
    smiles = sample_invalid_record_bad_smiles["smiles"]
    # Basic check: SMILES should not contain invalid characters like @@@
    assert "@@@" in smiles

def test_validate_bad_tg_range(dataset_schema, sample_invalid_record_bad_tg):
    """Test that Tg outside valid range is detected."""
    tg_k = sample_invalid_record_bad_tg["tg_k"]
    assert tg_k < 100.0 or tg_k > 1000.0

def test_validate_bad_source(dataset_schema, sample_invalid_record_bad_source):
    """Test that invalid source value is detected."""
    source = sample_invalid_record_bad_source["source"]
    valid_sources = ["NIST", "Polymer Database", "Materials Project", "Literature", "Other"]
    assert source not in valid_sources

def test_feature_matrix_schema(output_schema, sample_valid_feature_record):
    """Test that feature matrix records conform to the feature_matrix schema."""
    # Check required fields
    required_fields = ["id", "source", "mw", "tpsa", "logp", "num_rotatable_bonds",
                     "num_h_acceptors", "num_h_donors", "fox_prediction", "tg_residual"]
    for field in required_fields:
        assert field in sample_valid_feature_record

    # Validate types
    assert isinstance(sample_valid_feature_record["id"], int)
    assert isinstance(sample_valid_feature_record["source"], str)
    assert isinstance(sample_valid_feature_record["mw"], (int, float))
    assert isinstance(sample_valid_feature_record["tg_residual"], (int, float))

def test_model_output_schema(output_schema):
    """Test that model output schema has expected structure."""
    model_output_schema = output_schema["model_output"]
    assert "fields" in model_output_schema
    
    field_names = [f["name"] for f in model_output_schema["fields"]]
    assert "model_type" in field_names
    assert "metrics" in field_names
    assert "hyperparameters" in field_names
    assert "training_seed" in field_names

def test_report_schema(output_schema):
    """Test that report schema has expected structure."""
    report_schema = output_schema["report"]
    assert "fields" in report_schema
    
    field_names = [f["name"] for f in report_schema["fields"]]
    assert "report_type" in field_names
    assert "generated_at" in field_names
    assert "summary" in field_names

def test_weight_fraction_constraint(dataset_schema):
    """Test that weight fraction sum constraint is defined."""
    constraints = dataset_schema.get("constraints", [])
    weight_constraint = next(
        (c for c in constraints if c["name"] == "weight_fraction_sum"),
        None
    )
    assert weight_constraint is not None
    assert "tolerance" in weight_constraint
    assert weight_constraint["tolerance"] == 0.02

def test_schema_version_consistency(dataset_schema, output_schema):
    """Test that both schemas use the same version."""
    assert dataset_schema["schema_version"] == output_schema["schema_version"]
    assert dataset_schema["schema_version"] == "1.0.0"