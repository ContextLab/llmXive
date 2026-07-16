"""
Contract test for fingerprint generation schema (T017).

This test validates that the fingerprint generation pipeline produces
outputs matching the expected schema defined in the project specifications.

It verifies:
1. The output file structure (Parquet format with specific columns).
2. Data types and ranges for fingerprint bits.
3. Consistency with the diverse dataset generated in T011.
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from data.preprocess import load_preprocessed_data
from data.fingerprints import generate_fingerprints, get_fingerprint_config


class TestFingerprintSchema:
    """Contract tests for fingerprint generation output schema."""

    @pytest.fixture(scope="class")
    def processed_data_path(self):
        """Path to the diverse dataset from T011."""
        return Path("data/derived/diverse_molecules.csv")

    @pytest.fixture(scope="class")
    def fingerprints_path(self):
        """Path to the generated fingerprints artifact."""
        return Path("data/derived/fingerprints.parquet")

    @pytest.fixture(scope="class", autouse=True)
    def setup_fingerprints(self, processed_data_path, fingerprints_path):
        """
        Ensure fingerprints are generated before running tests.
        This fixture runs the generation pipeline if the file doesn't exist.
        """
        if not processed_data_path.exists():
            pytest.skip("Preprocessed data (T011) not found. Run T011 first.")

        if not fingerprints_path.exists():
            # Generate fingerprints if they don't exist
            # Note: In a real CI/CD, this would be a separate step
            print("Generating fingerprints for schema validation...")
            try:
                generate_fingerprints(str(processed_data_path))
            except Exception as e:
                pytest.fail(f"Failed to generate fingerprints: {e}")

    def test_file_exists(self, fingerprints_path):
        """Verify the output file exists."""
        assert fingerprints_path.exists(), "Fingerprints file not found"

    def test_parquet_format(self, fingerprints_path):
        """Verify the file is a valid Parquet file."""
        try:
            df = pd.read_parquet(fingerprints_path)
            assert df is not None
        except Exception as e:
            pytest.fail(f"Invalid Parquet file: {e}")

    def test_required_columns(self, fingerprints_path):
        """Verify all required columns are present."""
        df = pd.read_parquet(fingerprints_path)
        required_columns = ["smiles", "molecule_id", "fingerprint_type", "fingerprint_data"]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        assert not missing_columns, f"Missing required columns: {missing_columns}"

    def test_fingerprint_types(self, fingerprints_path):
        """Verify only expected fingerprint types are present."""
        df = pd.read_parquet(fingerprints_path)
        allowed_types = ["ECFP4", "MACCS", "FP2"]
        
        present_types = df["fingerprint_type"].unique().tolist()
        invalid_types = [t for t in present_types if t not in allowed_types]
        
        assert not invalid_types, f"Unexpected fingerprint types: {invalid_types}"

    def test_fingerprint_data_type(self, fingerprints_path):
        """Verify fingerprint data is stored as lists/arrays of integers."""
        df = pd.read_parquet(fingerprints_path)
        
        for fp_type in df["fingerprint_type"].unique():
            subset = df[df["fingerprint_type"] == fp_type]
            first_fp = subset.iloc[0]["fingerprint_data"]
            
            # Should be a list or numpy array
            assert isinstance(first_fp, (list, np.ndarray)), \
                f"Fingerprint data for {fp_type} is not a list/array"
            
            # Should contain integers (0 or 1)
            if len(first_fp) > 0:
                assert all(isinstance(x, (int, np.integer)) for x in first_fp), \
                    f"Fingerprint data for {fp_type} contains non-integer values"

    def test_fingerprint_lengths(self, fingerprints_path):
        """Verify fingerprint lengths match expected sizes."""
        df = pd.read_parquet(fingerprints_path)
        expected_lengths = {
            "ECFP4": 2048,
            "MACCS": 167,
            "FP2": 1024
        }
        
        for fp_type, expected_len in expected_lengths.items():
            subset = df[df["fingerprint_type"] == fp_type]
            if len(subset) == 0:
                continue
                
            first_fp = subset.iloc[0]["fingerprint_data"]
            actual_len = len(first_fp)
            
            assert actual_len == expected_len, \
                f"{fp_type} fingerprint length mismatch: expected {expected_len}, got {actual_len}"

    def test_no_duplicate_molecules(self, fingerprints_path):
        """Verify each molecule appears once per fingerprint type."""
        df = pd.read_parquet(fingerprints_path)
        
        for fp_type in df["fingerprint_type"].unique():
            subset = df[df["fingerprint_type"] == fp_type]
            duplicates = subset[subset.duplicated(subset=["molecule_id"], keep=False)]
            
            assert len(duplicates) == 0, \
                f"Duplicate molecules found for {fp_type}: {duplicates['molecule_id'].tolist()[:5]}"

    def test_fingerprint_bits_in_range(self, fingerprints_path):
        """Verify all fingerprint bits are 0 or 1."""
        df = pd.read_parquet(fingerprints_path)
        
        for fp_type in df["fingerprint_type"].unique():
            subset = df[df["fingerprint_type"] == fp_type]
            
            for _, row in subset.iterrows():
                fp_data = row["fingerprint_data"]
                unique_values = set(fp_data)
                
                assert unique_values.issubset({0, 1}), \
                    f"Invalid values in {fp_type} fingerprint: {unique_values}"

    def test_smiles_consistency(self, fingerprints_path, processed_data_path):
        """Verify SMILES in fingerprints match the source data."""
        fp_df = pd.read_parquet(fingerprints_path)
        source_df = load_preprocessed_data(str(processed_data_path))
        
        # Get unique SMILES from both
        fp_smiles = set(fp_df["smiles"].unique())
        source_smiles = set(source_df["smiles"].unique())
        
        # All fingerprint SMILES should be in source
        missing = fp_smiles - source_smiles
        assert not missing, f"SMILES in fingerprints not found in source: {missing}"

    def test_metadata_columns(self, fingerprints_path):
        """Verify metadata columns are present and non-null."""
        df = pd.read_parquet(fingerprints_path)
        
        # Check for non-null values in required columns
        required_non_null = ["smiles", "molecule_id", "fingerprint_type"]
        
        for col in required_non_null:
            assert df[col].notnull().all(), f"Null values found in column: {col}"

    def test_fingerprint_generation_config(self):
        """Verify the fingerprint generation configuration is valid."""
        config = get_fingerprint_config()
        
        assert "fingerprints" in config, "Missing 'fingerprints' in config"
        assert "ecfp4" in config["fingerprints"], "Missing ECFP4 config"
        assert "maccs" in config["fingerprints"], "Missing MACCS config"
        assert "fp2" in config["fingerprints"], "Missing FP2 config"
        
        # Verify priority order
        assert config["priority"] == ["ECFP4", "MACCS", "FP2"], \
            "Incorrect priority order in config"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])