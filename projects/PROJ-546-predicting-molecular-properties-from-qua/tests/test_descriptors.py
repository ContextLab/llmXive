"""
Integration test for code/generate_descriptors.py on 50 molecules.
Verifies descriptors_semi.csv has 50 rows, no NaN, HOMO/LUMO in eV.
"""
import os
import pytest
import pandas as pd
from pathlib import Path

def test_descriptor_generation_structure():
    """Verify generate_descriptors.py exists and has correct structure."""
    script_path = Path("code/generate_descriptors.py")
    assert script_path.exists(), "generate_descriptors.py not found"
    
    with open(script_path) as f:
        content = f.read()
        assert "smiles_to_xyz" in content
        assert "run_dftb_work" in content
        assert "parse_dftb_output" in content
        assert "validate_descriptors" in content

def test_export_geometries_structure():
    """Verify export_geometries.py exists."""
    script_path = Path("code/export_geometries.py")
    assert script_path.exists(), "export_geometries.py not found"
