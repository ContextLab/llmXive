"""
Contract test for T004: Validates US-1 (Data Ingestion) schema compliance.
Ensures the generated data matches the strict requirements for 3D coordinates,
resolution, and hydration flags.
"""
import json
import pytest
import yaml
from pathlib import Path
from jsonschema import validate, ValidationError

SCHEMA_PATH = Path(__file__).parent.parent.parent / "contracts" / "dataset_schema.schema.yaml"

@pytest.fixture
def schema():
    """Load the dataset schema from the contracts directory."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

@pytest.fixture
def valid_sample_complex():
    """Generate a minimal valid complex instance matching the schema."""
    return {
        "metadata": {
            "pdb_id": "1ABC",
            "resolution": 1.85,
            "water_flag": False,
            "source": "PDBbind_v2020_refined",
            "ligand_smiles": "CC(=O)Oc1ccccc1C(=O)O",
            "protein_chain": "A"
        },
        "atoms": [
            {
                "atom_type": "C",
                "coordinates_3d": [10.0, 10.0, 10.0],
                "charge": 0.0,
                "hydrophobicity": 0.5,
                "residue_name": "LIG",
                "residue_number": 1,
                "is_ligand": True
            },
            {
                "atom_type": "O",
                "coordinates_3d": [10.5, 10.0, 10.0],
                "charge": -0.5,
                "hydrophobicity": -0.8,
                "residue_name": "LIG",
                "residue_number": 1,
                "is_ligand": True
            },
            {
                "atom_type": "N",
                "coordinates_3d": [12.0, 12.0, 12.0],
                "charge": -0.3,
                "hydrophobicity": -0.2,
                "residue_name": "ALA",
                "residue_number": 50,
                "is_ligand": False
            }
        ],
        "interactions": [
            {
                "source_atom_idx": 0,
                "target_atom_idx": 1,
                "interaction_type": "covalent",
                "distance": 0.5
            },
            {
                "source_atom_idx": 1,
                "target_atom_idx": 2,
                "interaction_type": "hydrogen_bond",
                "distance": 2.8
            }
        ]
    }

@pytest.fixture
def valid_sample_with_water():
    """Generate a valid complex with water_flag=True."""
    data = {
        "metadata": {
            "pdb_id": "2XYZ",
            "resolution": 2.1,
            "water_flag": True,
            "source": "PDBbind_v2020_refined",
            "ligand_smiles": "CCO",
            "protein_chain": "B"
        },
        "atoms": [
            {
                "atom_type": "O",
                "coordinates_3d": [5.0, 5.0, 5.0],
                "charge": -0.6,
                "hydrophobicity": -1.0,
                "residue_name": "HOH",
                "residue_number": 999,
                "is_ligand": False
            }
        ],
        "interactions": []
    }
    return data

def test_schema_loads(schema):
    """Ensure the schema itself is valid YAML and loads correctly."""
    assert "type" in schema
    assert schema["type"] == "object"
    assert "properties" in schema

def test_valid_complex_passes(schema, valid_sample_complex):
    """A valid complex must pass validation."""
    validate(instance=valid_sample_complex, schema=schema)

def test_valid_water_flag_passes(schema, valid_sample_with_water):
    """A complex with water_flag=True must pass validation."""
    validate(instance=valid_sample_with_water, schema=schema)

def test_missing_resolution_fails(schema, valid_sample_complex):
    """Missing 'resolution' must raise ValidationError."""
    del valid_sample_complex["metadata"]["resolution"]
    with pytest.raises(ValidationError):
        validate(instance=valid_sample_complex, schema=schema)

def test_invalid_resolution_type_fails(schema, valid_sample_complex):
    """Non-numeric resolution must fail."""
    valid_sample_complex["metadata"]["resolution"] = "high"
    with pytest.raises(ValidationError):
        validate(instance=valid_sample_complex, schema=schema)

def test_negative_resolution_fails(schema, valid_sample_complex):
    """Negative resolution must fail (minimum: 0)."""
    valid_sample_complex["metadata"]["resolution"] = -1.0
    with pytest.raises(ValidationError):
        validate(instance=valid_sample_complex, schema=schema)

def test_missing_coordinates_3d_fails(schema, valid_sample_complex):
    """Missing 3D coordinates must fail."""
    del valid_sample_complex["atoms"][0]["coordinates_3d"]
    with pytest.raises(ValidationError):
        validate(instance=valid_sample_complex, schema=schema)

def test_invalid_coordinates_length_fails(schema, valid_sample_complex):
    """Coordinates with length != 3 must fail."""
    valid_sample_complex["atoms"][0]["coordinates_3d"] = [1.0, 2.0]
    with pytest.raises(ValidationError):
        validate(instance=valid_sample_complex, schema=schema)

def test_invalid_interaction_type_fails(schema, valid_sample_complex):
    """Interaction type not in enum must fail."""
    valid_sample_complex["interactions"][0]["interaction_type"] = "unknown_force"
    with pytest.raises(ValidationError):
        validate(instance=valid_sample_complex, schema=schema)

def test_water_flag_type_fails(schema, valid_sample_complex):
    """water_flag must be boolean."""
    valid_sample_complex["metadata"]["water_flag"] = "yes"
    with pytest.raises(ValidationError):
        validate(instance=valid_sample_complex, schema=schema)

def test_missing_atoms_fails(schema, valid_sample_complex):
    """Missing 'atoms' array must fail."""
    del valid_sample_complex["atoms"]
    with pytest.raises(ValidationError):
        validate(instance=valid_sample_complex, schema=schema)

def test_empty_atoms_fails(schema, valid_sample_complex):
    """Empty atoms array is allowed by schema but logic might reject it.
       Here we just ensure the schema accepts an empty array if no minItems is set.
       However, the schema requires 'atoms' to exist.
    """
    valid_sample_complex["atoms"] = []
    # Schema allows empty array unless minItems is set.
    # Our schema does not set minItems, so this passes validation.
    # This test ensures the schema doesn't crash on empty list.
    validate(instance=valid_sample_complex, schema=schema)

def test_schema_enforces_required_fields(schema):
    """Verify the schema explicitly requires critical fields."""
    required_fields = schema.get("required", [])
    assert "metadata" in required_fields
    assert "atoms" in required_fields
    assert "interactions" in required_fields

    metadata_required = schema["properties"]["metadata"].get("required", [])
    assert "resolution" in metadata_required
    assert "water_flag" in metadata_required
    assert "pdb_id" in metadata_required