"""
Unit tests for the NIST reference data generation script.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import hashlib
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from data.raw.generate_nist_refs import main, compute_file_hash, REFERENCE_DATA

def test_reference_data_structure():
    """Test that the reference data has the expected structure."""
    assert "metadata" in REFERENCE_DATA
    assert "solvents" in REFERENCE_DATA
    assert "water" in REFERENCE_DATA["solvents"]
    assert "ethanol" in REFERENCE_DATA["solvents"]
    assert "acetone" in REFERENCE_DATA["solvents"]

    # Check keys in solvents
    for solvent in ["water", "ethanol", "acetone"]:
        assert "chemical_formula" in REFERENCE_DATA["solvents"][solvent]
        assert "cas_number" in REFERENCE_DATA["solvents"][solvent]
        assert "diffusion_coefficients" in REFERENCE_DATA["solvents"][solvent]
        assert "298K" in REFERENCE_DATA["solvents"][solvent]["diffusion_coefficients"]
        assert "300K" in REFERENCE_DATA["solvents"][solvent]["diffusion_coefficients"]

        # Check value and unit
        for temp in ["298K", "300K"]:
            assert "value" in REFERENCE_DATA["solvents"][solvent]["diffusion_coefficients"][temp]
            assert "unit" in REFERENCE_DATA["solvents"][solvent]["diffusion_coefficients"][temp]
            assert REFERENCE_DATA["solvents"][solvent]["diffusion_coefficients"][temp]["unit"] == "m^2/s"

def test_compute_file_hash():
    """Test the file hash computation function."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test content")
        tmp_path = tmp.name

    try:
        expected_hash = hashlib.sha256(b"test content").hexdigest()
        actual_hash = compute_file_hash(tmp_path)
        assert actual_hash == expected_hash
    finally:
        os.unlink(tmp_path)

def test_json_serialization():
    """Test that the reference data can be serialized to JSON."""
    try:
        json_str = json.dumps(REFERENCE_DATA, indent=2)
        parsed = json.loads(json_str)
        assert parsed == REFERENCE_DATA
    except TypeError as e:
        pytest.fail(f"Reference data is not JSON serializable: {e}")

def test_values_are_realistic():
    """Test that diffusion coefficients are within realistic ranges (m^2/s)."""
    # Typical diffusion coefficients for small molecules in water are ~1e-9 to 1e-10 m^2/s
    # Acetone is faster, water is slower, ethanol is in between.
    # These are rough checks to ensure no order-of-magnitude errors.
    for solvent in ["water", "ethanol", "acetone"]:
        for temp in ["298K", "300K"]:
            val = REFERENCE_DATA["solvents"][solvent]["diffusion_coefficients"][temp]["value"]
            assert 1e-12 < val < 1e-7, f"Value for {solvent} at {temp} ({val}) is out of realistic range."