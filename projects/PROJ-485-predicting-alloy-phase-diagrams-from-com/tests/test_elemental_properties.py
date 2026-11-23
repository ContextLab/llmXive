import os
import csv
import pytest

# Ensure the data directory exists for the test to find the file
# In a real run, T001 ensures this directory exists.
DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'elemental_properties.csv')

REQUIRED_COLUMNS = ['element', 'atomic_radius_angstrom', 'electronegativity_pauling', 'valence_electrons']
REQUIRED_ELEMENTS = {'Cu', 'Al', 'Zn', 'Fe', 'C'}

def test_elemental_properties_file_exists():
    """Verify the CSV file exists."""
    assert os.path.isfile(DATA_PATH), f"File not found: {DATA_PATH}"

def test_elemental_properties_schema():
    """Verify the CSV has the correct columns."""
    with open(DATA_PATH, 'r', newline='') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        assert headers is not None, "CSV file is empty or has no headers"
        for col in REQUIRED_COLUMNS:
            assert col in headers, f"Missing required column: {col}"

def test_required_elements_present():
    """Verify all required elements are present."""
    elements = set()
    with open(DATA_PATH, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            elements.add(row['element'])
    
    assert REQUIRED_ELEMENTS.issubset(elements), f"Missing elements: {REQUIRED_ELEMENTS - elements}"

def test_numeric_values_valid():
    """Verify numeric columns contain valid floats."""
    with open(DATA_PATH, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Check atomic_radius
            try:
                radius = float(row['atomic_radius_angstrom'])
                assert radius > 0, f"Invalid radius for {row['element']}: {radius}"
            except ValueError:
                pytest.fail(f"Non-numeric atomic_radius for {row['element']}")
            
            # Check electronegativity
            try:
                en = float(row['electronegativity_pauling'])
                assert en > 0, f"Invalid electronegativity for {row['element']}: {en}"
            except ValueError:
                pytest.fail(f"Non-numeric electronegativity for {row['element']}")
            
            # Check valence electrons
            try:
                valence = int(row['valence_electrons'])
                assert valence > 0, f"Invalid valence electrons for {row['element']}: {valence}"
            except ValueError:
                pytest.fail(f"Non-integer valence electrons for {row['element']}")