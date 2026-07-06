import os
import sys
import pytest
import csv
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_ingestion import generate_synthetic_dataset, SyntheticDataError, ATOMIC_RADII

def test_generate_synthetic_dataset_creates_file():
    """Test that the synthetic dataset is created and has correct structure."""
    output_path = "data/raw/test_synthetic_fallback.csv"
    try:
        generate_synthetic_dataset(num_samples=10, output_path=output_path)
        # If we reach here, the halt didn't happen, which is unexpected for the main logic
        # but the file should exist.
        assert False, "Expected SyntheticDataError to be raised"
    except SyntheticDataError:
        # Expected behavior
        pass
    finally:
        # Verify file exists
        assert Path(output_path).exists(), "Synthetic fallback file was not created"
        
        # Verify content
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 10, f"Expected 10 rows, got {len(rows)}"
            
            required_cols = ["composition", "gfa_label", "delta", "delta_Hmix", "num_components"]
            assert all(col in reader.fieldnames for col in required_cols), "Missing required columns"
            
            # Check data types and basic logic
            for row in rows:
                assert row["gfa_label"] in ["Glass", "Crystalline"]
                assert float(row["delta"]) > 0
                assert int(row["num_components"]) >= 3

def test_inoue_rules_atomic_size():
    """Test that generated samples have non-zero atomic size difference."""
    # This is implicitly tested in the file creation, but we can check the function directly
    # Sample: Zr50Cu50
    sample = {"Zr": 0.5, "Cu": 0.5}
    # We need to import the helper if it were public, but it's internal.
    # We rely on the file content test for this.
    pass

def test_synthetic_mode_halt():
    """Test that the pipeline halts with the correct error."""
    try:
        generate_synthetic_dataset(num_samples=5, output_path="data/raw/halt_test.csv")
        assert False, "Should have raised SyntheticDataError"
    except SyntheticDataError as e:
        assert "SYNTHETIC_ONLY" in str(e)
        assert "halted" in str(e).lower()
