"""
Unit tests for T032c: verify_nesting logic.
"""
import os
import json
import tempfile
from pathlib import Path
import pandas as pd
import pytest
import sys

# Add code to path if running from tests
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from verify_nesting import verify_nesting, load_subset_indices

@pytest.fixture
def temp_dirs():
    with tempfile.TemporaryDirectory() as tmp_dir:
        processed_dir = Path(tmp_dir) / "processed"
        metadata_dir = Path(tmp_dir) / "metadata"
        processed_dir.mkdir()
        metadata_dir.mkdir()
        yield processed_dir, metadata_dir

def test_load_subset_indices():
    """Test loading indices from a CSV."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = Path(tmp_dir) / "test.csv"
        # Create a dummy CSV
        df = pd.DataFrame({"material_id": ["m1", "m2", "m3"]})
        df.to_csv(file_path, index=False)
        
        result = load_subset_indices(file_path)
        assert result == {"m1", "m2", "m3"}

def test_strict_netting_pass(temp_dirs):
    """Test a scenario where nesting is correct."""
    processed_dir, metadata_dir = temp_dirs
    
    # Create 100% set
    df_100 = pd.DataFrame({"material_id": [f"m{i}" for i in range(100)]})
    df_100.to_csv(processed_dir / "sparsity_100pct.csv", index=False)
    
    # Create 50% set (subset of 100%)
    df_50 = df_100.iloc[:50]
    df_50.to_csv(processed_dir / "sparsity_50pct.csv", index=False)
    
    # Create 25% set (subset of 50%)
    df_25 = df_50.iloc[:25]
    df_25.to_csv(processed_dir / "sparsity_25pct.csv", index=False)
    
    # Note: We only test the levels that exist in the files, 
    # but the function expects specific levels. 
    # For this unit test, we'll manually adjust the list or just test the logic.
    # Since the function uses a global SPARSITY_LEVELS, we can't easily mock it
    # without patching. We will test the logic by creating the expected files.
    
    # Actually, the function iterates SPARSITY_LEVELS. If a file is missing, it marks fail.
    # To test "pass", we must create all expected files.
    # Let's create dummy files for all levels to ensure the test runs fully.
    for level in [1, 2, 5, 10]:
        # Create a subset of the 25% set
        subset_size = int(25 * (level / 25)) 
        if subset_size == 0: subset_size = 1
        df_level = df_25.iloc[:subset_size]
        df_level.to_csv(processed_dir / f"sparsity_{level}pct.csv", index=False)

    result = verify_nesting(processed_dir, metadata_dir, None)
    assert result["is_strictly_nested"] is True
    assert "PASSED" in str(result["details"]).upper() or result["details"]

def test_nesting_fail_missing_subset(temp_dirs):
    """Test a scenario where nesting fails because a smaller set has an ID not in the larger set."""
    processed_dir, metadata_dir = temp_dirs
    
    # Create 100% set
    df_100 = pd.DataFrame({"material_id": [f"m{i}" for i in range(100)]})
    df_100.to_csv(processed_dir / "sparsity_100pct.csv", index=False)
    
    # Create 50% set with an ID NOT in 100% set
    df_50 = pd.DataFrame({"material_id": [f"m{i}" for i in range(50)] + ["m999"]})
    df_50.to_csv(processed_dir / "sparsity_50pct.csv", index=False)
    
    # Fill other levels to avoid missing file errors
    for level in [1, 2, 5, 10, 25]:
        # Create a valid subset of 50% (ignoring the bad ID for simplicity in this test)
        # Actually, if 50% is bad, 25% (subset of 50%) might still be valid relative to 50%
        # But 50% vs 100% is the failure point.
        df_level = df_50.iloc[:max(1, int(50 * (level/50)))]
        df_level.to_csv(processed_dir / f"sparsity_{level}pct.csv", index=False)

    result = verify_nesting(processed_dir, metadata_dir, None)
    assert result["is_strictly_nested"] is False
    # Check that the error is detected
    errors = [d for d in result["details"] if d.get("status") == "fail"]
    assert len(errors) > 0