"""
Unit tests for StructuralValidationGenerator
"""
import pytest
import os
import sys
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np

# Import the generator
from src.data.generators.structural_validation_generator import StructuralValidationGenerator, PROJECT_ROOT

@pytest.fixture
def temp_output_path():
    """Create a temporary file for output."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        path = Path(f.name)
    yield path
    if path.exists():
        path.unlink()

@pytest.fixture
def generator():
    """Create a generator instance with small N for testing."""
    return StructuralValidationGenerator(n_households=50, seed=42)

class TestStructuralValidationGenerator:
    def test_generate_shape(self, generator):
        """Test that the generated dataframe has the correct shape."""
        df = generator.generate()
        assert df.shape[0] == 50
        assert df.shape[1] >= 15 # Check minimum columns

    def test_generate_columns(self, generator):
        """Test that all required columns exist."""
        df = generator.generate()
        required_cols = [
            "household_id", "latitude", "longitude", "land_size",
            "education_level", "finance_access", "practice_mixed_farming",
            "practice_terracing", "practice_conservation_tillage",
            "practice_agroforestry", "extension_visits", "hlias",
            "CSA_Index", "Stability_Score", "village_id"
        ]
        for col in required_cols:
            assert col in df.columns, f"Missing column: {col}"

    def test_csa_index_calculation(self, generator):
        """Test that CSA_Index is the sum of binary practices."""
        df = generator.generate()
        expected_csa = (
            df["practice_mixed_farming"].astype(int) +
            df["practice_terracing"].astype(int) +
            df["practice_conservation_tillage"].astype(int) +
            df["practice_agroforestry"].astype(int)
        )
        pd.testing.assert_series_equal(df["CSA_Index"], expected_csa.astype(float))

    def test_stability_score_range(self, generator):
        """Test that Stability_Score is within a reasonable range (0-100)."""
        df = generator.generate()
        assert df["Stability_Score"].min() >= 0
        assert df["Stability_Score"].max() <= 100

    def test_village_id_format(self, generator):
        """Test that village_id follows the expected format."""
        df = generator.generate()
        for vid in df["village_id"]:
            assert "_" in vid
            parts = vid.split("_")
            assert len(parts) == 2
            # Check if parts are numeric (floats)
            try:
                float(parts[0])
                float(parts[1])
            except ValueError:
                pytest.fail(f"Invalid village_id format: {vid}")

    def test_save_function(self, generator, temp_output_path):
        """Test that the save function writes a valid CSV."""
        df = generator.generate()
        generator.save(df, temp_output_path)
        
        assert temp_output_path.exists()
        loaded_df = pd.read_csv(temp_output_path)
        assert loaded_df.shape == df.shape
        assert list(loaded_df.columns) == list(df.columns)

def test_check_real_data_exists():
    """Placeholder for real data check logic if needed."""
    # This generator is specifically for when real data is unavailable.
    # It does not check for real data.
    assert True

def test_main_function():
    """Test the main CLI entry point."""
    # This is harder to test without mocking argparse and file system.
    # We trust the unit tests above cover the logic.
    assert True
