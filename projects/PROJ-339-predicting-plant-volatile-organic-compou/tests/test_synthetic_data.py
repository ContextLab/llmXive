"""
Tests for the synthetic data generator (T005).

Verifies:
1. The generator creates the expected output file.
2. The output file has the correct number of rows (>= 50).
3. The output file contains the required columns.
4. The data types are correct.
5. The checksum manifest is generated.
"""
import os
import json
import csv
import pytest
from pathlib import Path
import pandas as pd

# Add code directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from generators.synthetic_data import generate_synthetic_dataset, compute_file_hash, validate_against_schema

class TestSyntheticDataGeneration:
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """Setup and teardown for each test."""
        self.tmp_dir = tmp_path
        self.output_path = self.tmp_dir / "test_synthetic_output.csv"
        yield
        # Cleanup handled by pytest tmp_path
    
    def test_file_creation(self):
        """Test that the generator creates the output file."""
        result = generate_synthetic_dataset(self.output_path)
        
        assert result.exists(), "Output file was not created"
        assert result.suffix == ".csv", "Output file is not a CSV"
        assert result.stat().st_size > 0, "Output file is empty"
        
    def test_minimum_row_count(self):
        """Test that the generator produces at least 50 rows."""
        generate_synthetic_dataset(self.output_path)
        
        df = pd.read_csv(self.output_path)
        
        assert len(df) >= 50, f"Expected >= 50 rows, got {len(df)}"
        
    def test_required_columns(self):
        """Test that all required schema columns are present."""
        generate_synthetic_dataset(self.output_path)
        
        df = pd.read_csv(self.output_path)
        
        required_cols = [
            "sample_id", "temperature", "light_intensity", "co2_level",
            "monoterpene_total", "sesquiterpene_total", "green_leaf_volatiles", "benzenoids"
        ]
        
        for col in required_cols:
            assert col in df.columns, f"Missing required column: {col}"
            
    def test_data_types(self):
        """Test that numeric columns are numeric and sample_id is string."""
        generate_synthetic_dataset(self.output_path)
        
        df = pd.read_csv(self.output_path)
        
        # Check sample_id is string
        assert df["sample_id"].dtype == 'object', "sample_id should be string"
        assert all(isinstance(x, str) for x in df["sample_id"]), "All sample_ids must be strings"
        
        # Check numeric columns
        numeric_cols = ["temperature", "light_intensity", "co2_level", "monoterpene_total"]
        for col in numeric_cols:
            assert pd.api.types.is_numeric_dtype(df[col]), f"{col} should be numeric"
            # Check for non-NaN values
            assert not df[col].isna().any(), f"{col} contains NaN values"
            
    def test_checksum_manifest(self):
        """Test that a checksum manifest is generated."""
        generate_synthetic_dataset(self.output_path)
        
        manifest_path = self.output_path.parent / "synthetic_data_hashes.json"
        
        assert manifest_path.exists(), "Checksum manifest was not created"
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
            
        assert "checksum" in manifest, "Manifest missing checksum"
        assert manifest["file"] == str(self.output_path), "Manifest file path mismatch"
        assert "num_samples" in manifest, "Manifest missing num_samples"
        assert manifest["num_samples"] >= 50, "Manifest num_samples < 50"
        
    def test_schema_validation(self):
        """Test the internal schema validation function."""
        generate_synthetic_dataset(self.output_path)
        
        df = pd.read_csv(self.output_path)
        data_list = df.to_dict('records')
        
        assert validate_against_schema(data_list), "Schema validation failed"
        
    def test_unique_sample_ids(self):
        """Test that all sample IDs are unique."""
        generate_synthetic_dataset(self.output_path)
        
        df = pd.read_csv(self.output_path)
        
        assert df["sample_id"].is_unique, "Sample IDs are not unique"
        assert len(df) == df["sample_id"].nunique(), "Duplicate sample IDs found"
        
    def test_consistent_seed(self):
        """Test that running with the same seed produces the same output."""
        # Run twice
        path1 = self.tmp_dir / "test_seed_1.csv"
        path2 = self.tmp_dir / "test_seed_2.csv"
        
        generate_synthetic_dataset(path1)
        generate_synthetic_dataset(path2)
        
        # Compare checksums
        hash1 = compute_file_hash(path1)
        hash2 = compute_file_hash(path2)
        
        assert hash1 == hash2, "Same seed did not produce identical output"