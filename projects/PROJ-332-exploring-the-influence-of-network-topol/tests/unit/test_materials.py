import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from material_db import get_material_conductivity, list_available_materials

def test_nist_defaults_trigger():
    k = get_material_conductivity("Si")
    assert k == 149.0

    k = get_material_conductivity("Ag")
    assert k == 429.0

def test_non_standard_material_error():
    with pytest.raises(ValueError) as excinfo:
        get_material_conductivity("UnknownMaterial")
    assert "not found in local store or NIST defaults" in str(excinfo.value)

def test_override_value():
    k = get_material_conductivity("Si", bulk_conductivity=200.0)
    assert k == 200.0
