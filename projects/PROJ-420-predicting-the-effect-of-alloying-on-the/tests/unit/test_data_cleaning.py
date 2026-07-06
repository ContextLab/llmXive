import pytest
import json
import tempfile
import os
from pathlib import Path
import numpy as np

from code.data_cleaning import (
    load_raw_data,
    verify_measurement_independence,
    filter_monolithic_alloys,
    check_major_element_sum,
    normalize_units,
    clean_data
)
from code.config import get_config

@pytest.fixture
def sample_raw_data():
    return [
        {
            "material_id": "mp-1",
            "elements": {"Al": 0.90, "Cu": 0.05, "Mg": 0.03, "Si": 0.02},
            "poissons_ratio": 0.34,
            "youngs_modulus": 70000000000, # 70 GPa in Pa
            "bulk_modulus": 75000000000,   # 75 GPa in Pa
            "measurement_method": "experiment",
            "measurement_source": "MP"
        },
        {
            "material_id": "mp-2",
            "elements": {"Al": 0.92, "Mg": 0.04, "Zn": 0.04},
            "poissons_ratio": 0.33,
            "youngs_modulus": 72, # Already GPa
            "bulk_modulus": 78,
            "measurement_method": "calculated",
            "measurement_source": "MP"
        },
        {
            "material_id": "mp-3",
            "elements": {"Al": 0.80, "Cu": 0.10, "Mg": 0.05},
            "poissons_ratio": 0.35,
            "youngs_modulus": 68,
            "bulk_modulus": 70,
            "measurement_method": "", # Missing method
            "measurement_source": "Unknown"
        }
    ]

@pytest.fixture
def temp_raw_file(sample_raw_data):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_raw_data, f)
        path = f.name
    yield path
    os.unlink(path)

def test_load_raw_data(temp_raw_file):
    data = load_raw_data([temp_raw_file])
    assert len(data) == 3

def test_verify_measurement_independence(sample_raw_data):
    # mp-1: experiment -> keep
    # mp-2: calculated -> exclude
    # mp-3: missing method, but check derived logic
    # nu = 0.5 * (1 - E/3K) = 0.5 * (1 - 68/210) = 0.5 * (1 - 0.3238) = 0.338
    # reported 0.35. Diff = 0.012. 0.012/0.35 = 3.4% > 1%. So it should NOT be excluded as derived.
    # However, task T014 says "if method is missing... exclude".
    # Let's re-read T014: "if method is missing... calculate... if matches exclude... if Bulk missing exclude".
    # It doesn't explicitly say to exclude if it doesn't match, but T014 says "query measurement_method... exclude if missing".
    # Actually T014 says: "exclude entries where the method is ... missing/unknown".
    # So mp-3 should be excluded because method is missing.
    
    filtered = verify_measurement_independence(sample_raw_data)
    # mp-2 excluded (calculated)
    # mp-3 excluded (missing method)
    # mp-1 kept
    assert len(filtered) == 1
    assert filtered[0]["material_id"] == "mp-1"

def test_filter_monolithic_alloys(sample_raw_data):
    # Assumes independence already checked
    # We need to pass data that has passed independence check
    # Let's simulate data with required fields
    data = [
        {
            "poissons_ratio": 0.34,
            "youngs_modulus_gpa": 70.0,
            "Cu": 0.05, "Mg": 0.03, "Si": 0.02, "Zn": 0.0, "Mn": 0.0, "Al": 0.90
        },
        {
            "poissons_ratio": 0.33,
            "youngs_modulus_gpa": 72.0,
            "Cu": None, "Mg": 0.04, "Si": 0.0, "Zn": 0.04, "Mn": 0.0, "Al": 0.92
        }
    ]
    filtered = filter_monolithic_alloys(data)
    assert len(filtered) == 1
    assert filtered[0]["material_id"] is None # We didn't set ID in this snippet

def test_check_major_element_sum():
    data = [
        {"Cu": 0.1, "Mg": 0.1, "Si": 0.1, "Zn": 0.1, "Mn": 0.1, "Al": 0.6}, # Sum = 1.0
        {"Cu": 0.1, "Mg": 0.1, "Si": 0.1, "Zn": 0.1, "Mn": 0.1, "Al": 0.4}  # Sum = 0.9
    ]
    valid = check_major_element_sum(data)
    assert len(valid) == 1
    assert valid[0]["Al"] == 0.6

def test_normalize_units():
    data = [
        {
            "youngs_modulus": 70000000000, # Pa
            "bulk_modulus": 75000000000,   # Pa
            "Cu": 5.0, "Mg": 3.0, "Si": 2.0, "Zn": 0.0, "Mn": 0.0, "Al": 90.0 # Percent, sum=100
        },
        {
            "youngs_modulus": 70.0, # GPa
            "bulk_modulus": 75.0,
            "Cu": 0.05, "Mg": 0.03, "Si": 0.02, "Zn": 0.0, "Mn": 0.0, "Al": 0.90 # Fractions
        }
    ]
    normalized = normalize_units(data)
    
    # Check first record
    assert normalized[0]["youngs_modulus_gpa"] == 70.0
    assert normalized[0]["Cu"] == 0.05 # 5/100
    assert abs(sum([normalized[0][k] for k in ["Cu", "Mg", "Si", "Zn", "Mn", "Al"]]) - 1.0) < 1e-6

    # Check second record
    assert normalized[1]["youngs_modulus_gpa"] == 70.0
    assert normalized[1]["Cu"] == 0.05
    assert abs(sum([normalized[1][k] for k in ["Cu", "Mg", "Si", "Zn", "Mn", "Al"]]) - 1.0) < 1e-6
