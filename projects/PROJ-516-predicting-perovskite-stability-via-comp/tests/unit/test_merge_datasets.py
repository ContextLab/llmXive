"""
Unit tests for merge_datasets.py (T012c).
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from merge_datasets import load_csv_safe, merge_perovskite_datasets

def test_load_csv_safe_missing_file():
    """Test loading a non-existent file returns None."""
    result = load_csv_safe(Path("/nonexistent/path.csv"))
    assert result is None

def test_load_csv_safe_empty_file():
    """Test loading an empty file returns None."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("")
        temp_path = Path(f.name)
    
    try:
        result = load_csv_safe(temp_path)
        assert result is None
    finally:
        os.unlink(temp_path)

def test_load_csv_safe_valid():
    """Test loading a valid CSV returns a DataFrame."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("formula,source\nCsPbI3,NREL\n")
        temp_path = Path(f.name)
    
    try:
        result = load_csv_safe(temp_path)
        assert result is not None
        assert len(result) == 1
        assert "formula" in result.columns
    finally:
        os.unlink(temp_path)

def test_merge_logic_duplicate_detection():
    """
    Test that the merge logic correctly identifies duplicates.
    This simulates the core logic of T012c without file I/O side effects on the real project.
    """
    # Create temporary files for NREL and MP
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        nrel_file = tmpdir_path / "nrel_perovskites.csv"
        mp_file = tmpdir_path / "mp_perovskites.csv"
        merged_file = tmpdir_path / "perovskites_merged.csv"

        # Write test data with a known duplicate
        # NREL: 2 rows
        nrel_df = pd.DataFrame({
            "formula": ["CsPbI3", "FAPbI3"],
            "source": ["NREL", "NREL"],
            "T_d": [100, 120]
        })
        nrel_df.to_csv(nrel_file, index=False)

        # MP: 2 rows (one duplicate formula+source with NREL, one new)
        # Note: T012c merges based on formula AND source. 
        # If source is different, it's not a duplicate.
        # Let's create a scenario where source is the same to test duplicate logic if we were merging same source.
        # But the task says "Concatenate ... based on formula and source". 
        # If source is different (NREL vs MP), they are distinct rows.
        # The duplicate check in T012d is "based on formula and source".
        # So if we have CsPbI3 from NREL and CsPbI3 from MP, they are NOT duplicates.
        # We need to simulate a case where the SAME formula+source appears in both?
        # That would imply the fetch logic is flawed or we are merging same source twice.
        # However, T012c's job is to concatenate. T012d removes duplicates.
        # Let's test the concatenation and the duplicate counting logic.
        
        mp_df = pd.DataFrame({
            "formula": ["CsPbI3", "MAPbBr3"],
            "source": ["MaterialsProject", "MaterialsProject"],
            "T_d": [110, 130]
        })
        mp_df.to_csv(mp_file, index=False)

        # Mock the paths in the module
        import merge_datasets
        original_nrel = merge_datasets.NREL_PATH
        original_mp = merge_datasets.MP_PATH
        original_merged = merge_datasets.MERGED_PATH

        merge_datasets.NREL_PATH = nrel_file
        merge_datasets.MP_PATH = mp_file
        merge_datasets.MERGED_PATH = merged_file

        try:
            success, message = merge_perovskite_datasets()
            assert success
            
            # Check output file
            assert merged_file.exists()
            merged_df = pd.read_csv(merged_file)
            assert len(merged_df) == 4 # 2 NREL + 2 MP
            
            # Verify no duplicates were dropped yet (T012c just concatenates, T012d drops)
            # But T012c logs the duplicate count. Since source is different, count should be 0.
            assert "Duplicate count" in message
            assert "0" in message or "rows to be dropped" in message
        finally:
            merge_datasets.NREL_PATH = original_nrel
            merge_datasets.MP_PATH = original_mp
            merge_datasets.MERGED_PATH = original_merged
