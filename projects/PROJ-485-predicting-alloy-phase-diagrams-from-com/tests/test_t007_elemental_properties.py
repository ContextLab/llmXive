"""
Test for T007: Verify elemental_properties.csv exists and contains correct data.
"""
import os
import csv
import pytest

# Project root setup
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
data_path = os.path.join(project_root, "data", "raw", "elemental_properties.csv")

@pytest.fixture
def elemental_data():
    """Load the CSV data for testing."""
    if not os.path.exists(data_path):
        pytest.fail(f"File not found: {data_path}")
    
    with open(data_path, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)

def test_file_exists():
    """Assert the file exists."""
    assert os.path.exists(data_path), f"File {data_path} does not exist."

def test_columns_present(elemental_data):
    """Assert required columns exist."""
    if not elemental_data:
        pytest.fail("File is empty.")
    
    required_columns = {"element", "atomic_radius_angstrom", "electronegativity_pauling", "valence_electrons"}
    actual_columns = set(elemental_data[0].keys())
    assert required_columns.issubset(actual_columns), f"Missing columns: {required_columns - actual_columns}"

def test_required_elements_present(elemental_data):
    """Assert rows for Cu, Al, Zn, Fe, C exist."""
    required_elements = {"Cu", "Al", "Zn", "Fe", "C"}
    actual_elements = {row["element"] for row in elemental_data}
    assert required_elements.issubset(actual_elements), f"Missing elements: {required_elements - actual_elements}"

def test_data_numeric_and_valid(elemental_data):
    """Assert numeric columns contain valid numbers."""
    for row in elemental_data:
        try:
            radius = float(row["atomic_radius_angstrom"])
            en = float(row["electronegativity_pauling"])
            valence = int(row["valence_electrons"])
            
            assert radius > 0, f"Invalid atomic radius for {row['element']}: {radius}"
            assert en > 0, f"Invalid electronegativity for {row['element']}: {en}"
            assert valence > 0, f"Invalid valence electrons for {row['element']}: {valence}"
        except (ValueError, TypeError) as e:
            pytest.fail(f"Non-numeric value in row {row['element']}: {e}")

def test_specific_values_correct(elemental_data):
    """Assert specific known values for Cu and C."""
    data_map = {row["element"]: row for row in elemental_data}
    
    # Check Cu (Copper)
    cu = data_map.get("Cu")
    assert cu is not None
    assert float(cu["atomic_radius_angstrom"]) == 1.28
    assert float(cu["electronegativity_pauling"]) == 1.90
    assert int(cu["valence_electrons"]) == 1

    # Check C (Carbon)
    c = data_map.get("C")
    assert c is not None
    assert float(c["atomic_radius_angstrom"]) == 0.77
    assert float(c["electronegativity_pauling"]) == 2.55
    assert int(c["valence_electrons"]) == 4
