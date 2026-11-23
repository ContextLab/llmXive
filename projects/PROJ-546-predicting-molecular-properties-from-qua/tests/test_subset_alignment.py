"""
Unit tests for T027: Subset Alignment Validation.

Verifies that the validation logic correctly identifies matching and mismatching
subsets of molecules between DFTB+ and DFT descriptor files.
"""
import csv
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add the code directory to the path for imports
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from validate_subset_alignment import load_smiles_set, compare_subsets, validate_subset_alignment

def create_temp_csv(filepath: Path, smiles_list: list):
    """Helper to create a temporary CSV file with SMILES."""
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['SMILES', 'value'])
        writer.writeheader()
        for smiles in smiles_list:
            writer.writerow({'SMILES': smiles, 'value': 0.0})

def test_load_smiles_set():
    """Test that load_smiles_set correctly reads SMILES from a CSV."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.csv"
        smiles_data = ["CCO", "CC", "c1ccccc1"]
        create_temp_csv(test_file, smiles_data)
        
        result = load_smiles_set(test_file)
        assert result == set(smiles_data)
        assert len(result) == 3

def test_compare_subsets_identical():
    """Test comparison when both sets are identical."""
    set_a = {"CCO", "CC", "c1ccccc1"}
    set_b = {"c1ccccc1", "CC", "CCO"} # Same elements, different order
    
    is_aligned, missing, extra, _ = compare_subsets(set_a, set_b, Path("a.csv"), Path("b.csv"))
    
    assert is_aligned is True
    assert len(missing) == 0
    assert len(extra) == 0

def test_compare_subsets_missing_in_dft():
    """Test comparison when DFT is missing molecules present in DFTB+."""
    semi_set = {"CCO", "CC", "c1ccccc1"}
    dft_set = {"CC", "c1ccccc1"} # Missing "CCO"
    
    is_aligned, missing, extra, _ = compare_subsets(semi_set, dft_set, Path("semi.csv"), Path("dft.csv"))
    
    assert is_aligned is False
    assert "CCO" in missing
    assert len(missing) == 1
    assert len(extra) == 0

def test_compare_subsets_extra_in_dft():
    """Test comparison when DFT has extra molecules not in DFTB+."""
    semi_set = {"CCO", "CC"}
    dft_set = {"CCO", "CC", "c1ccccc1"} # Extra "c1ccccc1"
    
    is_aligned, missing, extra, _ = compare_subsets(semi_set, dft_set, Path("semi.csv"), Path("dft.csv"))
    
    assert is_aligned is False
    assert len(missing) == 0
    assert "c1ccccc1" in extra

def test_validate_subset_alignment_integration():
    """Integration test for the full validation function."""
    with tempfile.TemporaryDirectory() as tmpdir:
        semi_path = Path(tmpdir) / "semi.csv"
        dft_path = Path(tmpdir) / "dft.csv"
        
        # Create matching files
        create_temp_csv(semi_path, ["CCO", "CC"])
        create_temp_csv(dft_path, ["CC", "CCO"])
        
        assert validate_subset_alignment(semi_path, dft_path, strict=True) is True

def test_validate_subset_alignment_mismatch():
    """Integration test for mismatched files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        semi_path = Path(tmpdir) / "semi.csv"
        dft_path = Path(tmpdir) / "dft.csv"
        
        # Create mismatching files
        create_temp_csv(semi_path, ["CCO", "CC"])
        create_temp_csv(dft_path, ["CC"]) # Missing "CCO"
        
        assert validate_subset_alignment(semi_path, dft_path, strict=True) is False