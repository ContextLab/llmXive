"""
Tests for the elemental properties verification logic (T006a).
"""
import os
import sys
import tempfile
import csv
import pytest

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from features.verify_elements import verify_elemental_properties, REFERENCE_VALUES

def create_temp_csv(rows, filename="test_elements.csv"):
    """Helper to create a temporary CSV file with given rows."""
    fd, path = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["element", "atomic_radius_angstrom", "electronegativity_pauling", "valence_electrons"])
        writer.writeheader()
        writer.writerows(rows)
    return path

def test_verify_success():
    """Test that valid data within 1% passes."""
    # Use exact reference values for Cu
    row = {
        "element": "Cu",
        "atomic_radius_angstrom": REFERENCE_VALUES["Cu"]["atomic_radius_angstrom"],
        "electronegativity_pauling": REFERENCE_VALUES["Cu"]["electronegativity_pauling"],
        "valence_electrons": REFERENCE_VALUES["Cu"]["valence_electrons"]
    }
    path = create_temp_csv([row])
    try:
        result = verify_elemental_properties(path)
        assert result is True
    finally:
        os.remove(path)

def test_verify_failure_deviation():
    """Test that data with >1% deviation fails."""
    # Introduce a 5% deviation in atomic radius for Cu
    ref_val = REFERENCE_VALUES["Cu"]["atomic_radius_angstrom"]
    bad_val = ref_val * 1.05  # 5% increase
    
    row = {
        "element": "Cu",
        "atomic_radius_angstrom": bad_val,
        "electronegativity_pauling": REFERENCE_VALUES["Cu"]["electronegativity_pauling"],
        "valence_electrons": REFERENCE_VALUES["Cu"]["valence_electrons"]
    }
    path = create_temp_csv([row])
    try:
        result = verify_elemental_properties(path)
        assert result is False
    finally:
        os.remove(path)

def test_verify_multiple_elements():
    """Test verification with multiple elements, one passing and one failing."""
    ref_cu = REFERENCE_VALUES["Cu"]
    ref_al = REFERENCE_VALUES["Al"]
    
    # Cu is correct
    row_cu = {
        "element": "Cu",
        "atomic_radius_angstrom": ref_cu["atomic_radius_angstrom"],
        "electronegativity_pauling": ref_cu["electronegativity_pauling"],
        "valence_electrons": ref_cu["valence_electrons"]
    }
    
    # Al has 2% deviation in electronegativity
    bad_en = ref_al["electronegativity_pauling"] * 1.02
    row_al = {
        "element": "Al",
        "atomic_radius_angstrom": ref_al["atomic_radius_angstrom"],
        "electronegativity_pauling": bad_en,
        "valence_electrons": ref_al["valence_electrons"]
    }
    
    path = create_temp_csv([row_cu, row_al])
    try:
        result = verify_elemental_properties(path)
        # Should fail because Al is bad
        assert result is False
    finally:
        os.remove(path)

def test_verify_missing_file():
    """Test that missing file returns False and logs error."""
    result = verify_elemental_properties("non_existent_file.csv")
    assert result is False
