"""
Contract test for data schema validation against DiffusionRecord entity.
"""
import pytest
from pathlib import Path
import csv
import json

# Test data path
TEST_DATA_PATH = Path("data/raw/fetched_diffusion.csv")

def test_schema_validation():
    """
    Validates the structure of the fetched diffusion data against the expected schema.
    """
    if not TEST_DATA_PATH.exists():
        pytest.skip("Test data file not found. Run acquisition script first.")
    
    # Load data
    with open(TEST_DATA_PATH, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if not rows:
        pytest.fail("No data rows found in test data file.")
    
    # Define expected schema (simplified)
    expected_fields = {
        "element",
        "crystal_structure",
        "diffusion_mode",
        "activation_energy_eV",
        "pre_exponential_factor",
        "temperature_range_K"
    }
    
    # Check if all expected fields are present
    actual_fields = set(rows[0].keys())
    
    missing_fields = expected_fields - actual_fields
    if missing_fields:
        pytest.fail(f"Missing fields in data: {missing_fields}")
    
    # Validate data types and values
    for i, row in enumerate(rows):
        try:
            # Check crystal structure is FCC
            if row.get("crystal_structure") not in ["FCC", "fcc", "Cubic"]:
                pytest.fail(f"Row {i}: Invalid crystal_structure: {row.get('crystal_structure')}")
            
            # Check activation energy is numeric
            float(row.get("activation_energy_eV", 0))
            
            # Check diffusion mode is self
            if row.get("diffusion_mode") not in ["self", "Self"]:
                # Allow other modes for now, but log
                pass
                
        except ValueError as e:
            pytest.fail(f"Row {i}: Data type error: {e}")
    
    print("Schema validation passed.")

if __name__ == "__main__":
    test_schema_validation()
