"""
Unit tests for the synthetic test data generator (T002d).
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path
import hashlib

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from generate_synthetic_test_data import generate_synthetic_dataset, hash_file_content

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"

class TestSyntheticDataGenerator:
    def test_generate_synthetic_dataset_structure(self):
        """Test that the generated dataset has the correct columns."""
        df = generate_synthetic_dataset(n_subjects=2, n_trials=2, n_samples_per_trial=10, seed=42)
        
        expected_columns = [
            "subject_id", "trial_id", "timestamp", "pupil_diameter",
            "x", "y", "search_time", "target_salience", "fixation_count"
        ]
        
        assert list(df.columns) == expected_columns
        assert len(df) > 0

    def test_generate_synthetic_dataset_values(self):
        """Test that the generated data contains reasonable values."""
        df = generate_synthetic_dataset(n_subjects=1, n_trials=1, n_samples_per_trial=5, seed=123)
        
        # Check numeric ranges
        assert df["pupil_diameter"].between(3.0, 7.0).all()
        assert df["search_time"].between(0.0, 10.0).all()
        assert df["target_salience"].between(0.0, 1.0).all()
        assert df["fixation_count"].between(1, 50).all()

    def test_hash_consistency(self):
        """Test that the same input produces the same hash."""
        df1 = generate_synthetic_dataset(seed=999)
        df2 = generate_synthetic_dataset(seed=999)
        
        # Convert to bytes for hashing
        csv1 = df1.to_csv(index=False).encode('utf-8')
        csv2 = df2.to_csv(index=False).encode('utf-8')
        
        hash1 = hashlib.sha256(csv1).hexdigest()
        hash2 = hashlib.sha256(csv2).hexdigest()
        
        assert hash1 == hash2

    def test_manifest_creation(self):
        """Test that the manifest file is created when running main."""
        # This is an integration test for the side effect of main()
        # We assume main() is called via subprocess in a real scenario,
        # but here we verify the logic exists.
        from generate_synthetic_test_data import write_test_artifacts_manifest
        
        # Just verify the function exists and can be called with dummy data
        test_path = PROJECT_ROOT / "data" / "raw" / "dummy.csv"
        test_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.write_text("dummy")
        
        try:
            write_test_artifacts_manifest(STATE_DIR / "test_artifacts.yaml", test_path, "dummy_hash")
            assert (STATE_DIR / "test_artifacts.yaml").exists()
        finally:
            if test_path.exists():
                test_path.unlink()
            # Clean up manifest if it was created just for this test
            manifest_path = STATE_DIR / "test_artifacts.yaml"
            if manifest_path.exists():
                # We don't delete the manifest here because other tests might rely on it,
                # but in a real CI environment, we would clean up.
                pass