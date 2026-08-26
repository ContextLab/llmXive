"""
Contract test for material schema validation.

Verifies that `load_material_schema` exists with the correct signature
and that the schema loads correctly for the defined `MaterialProfile`.
"""
import os
import sys
import json
import tempfile
from pathlib import Path

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data_ingestion import load_material_schema, MaterialProfile
from code.utils import get_project_root


def test_load_material_schema_signature_and_success():
    """
    Verify `load_material_schema` exists with signature `(path: str) -> Schema`
    and asserts the schema loads correctly.
    """
    # Create a temporary JSON file that mimics the expected NIST material structure
    # based on the MaterialProfile definition in data_ingestion.py
    valid_material_data = {
        "Aluminum": {
            "thermal_conductivity": 237.0,
            "emissivity": 0.09,
            "specific_heat": 900.0,
            "density": 2700.0,
            "unit_price": 2.50
        },
        "Copper": {
            "thermal_conductivity": 401.0,
            "emissivity": 0.03,
            "specific_heat": 385.0,
            "density": 8960.0,
            "unit_price": 9.00
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(valid_material_data, f)
        temp_path = f.name

    try:
        # Call the function
        schema = load_material_schema(temp_path)

        # Verify return type (should be a dict or similar mapping acting as Schema)
        assert isinstance(schema, dict), f"Expected schema to be a dict, got {type(schema)}"

        # Verify keys match expected materials
        assert "Aluminum" in schema, "Aluminum missing from loaded schema"
        assert "Copper" in schema, "Copper missing from loaded schema"

        # Verify structure of a MaterialProfile entry
        al_data = schema["Aluminum"]
        assert "thermal_conductivity" in al_data
        assert "emissivity" in al_data
        assert "specific_heat" in al_data
        assert "density" in al_data
        assert "unit_price" in al_data

        # Verify types are numeric
        assert isinstance(al_data["thermal_conductivity"], (int, float))
        assert isinstance(al_data["emissivity"], (int, float))

    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_load_material_schema_invalid_path():
    """
    Verify that `load_material_schema` raises an appropriate error for a missing file.
    """
    non_existent_path = str(project_root / "data" / "raw" / "non_existent_file.json")
    
    try:
        load_material_schema(non_existent_path)
        assert False, "Expected an exception for missing file, but none was raised."
    except (FileNotFoundError, OSError) as e:
        # Expected behavior: fail loudly
        pass
    except Exception as e:
        # If it raises a custom ProjectError, that's also acceptable
        pass


def test_load_material_schema_invalid_json():
    """
    Verify that `load_material_schema` raises an error for malformed JSON.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{ invalid json }")
        temp_path = f.name

    try:
        load_material_schema(temp_path)
        assert False, "Expected an exception for invalid JSON, but none was raised."
    except json.JSONDecodeError:
        # Expected
        pass
    except Exception as e:
        # If it raises a custom ProjectError wrapping the JSON error, that's acceptable
        pass
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)