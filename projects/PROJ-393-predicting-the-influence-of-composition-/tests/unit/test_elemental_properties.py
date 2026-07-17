import csv
import os
from pathlib import Path
import pytest

# Path resolution relative to test file location
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FILE = PROJECT_ROOT / "data" / "raw" / "elemental_properties.csv"

REQUIRED_ELEMENTS = ["Mn", "Co", "Fe", "Ga", "Al", "Ni", "Cu", "Sn", "In", "Ti", "V"]
REQUIRED_COLUMNS = ["element", "electronegativity", "atomic_radii", "valence_electrons"]

@pytest.fixture(scope="module")
def data_rows():
    """Load the CSV data once for the test module."""
    if not DATA_FILE.exists():
        pytest.skip(f"Data file {DATA_FILE} not found. Run the generation script first.")
    
    with open(DATA_FILE, mode='r') as f:
        reader = csv.DictReader(f)
        return list(reader)

def test_file_exists():
    assert DATA_FILE.exists(), "elemental_properties.csv must exist in data/raw/"

def test_required_columns_present(data_rows):
    if not data_rows:
        pytest.skip("No data rows found.")
    header = data_rows[0].keys()
    for col in REQUIRED_COLUMNS:
        assert col in header, f"Column '{col}' is missing from the CSV."

def test_required_elements_present(data_rows):
    if not data_rows:
        pytest.skip("No data rows found.")
    elements = [row['element'] for row in data_rows]
    for elem in REQUIRED_ELEMENTS:
        assert elem in elements, f"Element '{elem}' is missing from the dataset."

def test_no_duplicate_elements(data_rows):
    if not data_rows:
        pytest.skip("No data rows found.")
    elements = [row['element'] for row in data_rows]
    assert len(elements) == len(set(elements)), "Duplicate elements found in the CSV."

def test_numeric_values_valid(data_rows):
    if not data_rows:
        pytest.skip("No data rows found.")
    
    for row in data_rows:
        # Electronegativity should be positive float
        en = float(row['electronegativity'])
        assert 0 < en < 4.0, f"Electronegativity {en} for {row['element']} seems out of range."
        
        # Atomic radii should be positive integer/float (in pm)
        ar = float(row['atomic_radii'])
        assert 50 < ar < 250, f"Atomic radii {ar} for {row['element']} seems out of range."
        
        # Valence electrons should be positive integer
        ve = int(row['valence_electrons'])
        assert 1 <= ve <= 12, f"Valence electrons {ve} for {row['element']} seems out of range."