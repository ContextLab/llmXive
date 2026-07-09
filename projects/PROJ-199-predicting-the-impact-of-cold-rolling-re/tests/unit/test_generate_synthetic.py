"""
Unit tests for the synthetic data generator (T011b).
"""
import pytest
import os
import sys
from pathlib import Path
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import ConfigurationError, get_reductions
from data.generate_synthetic import generate_synthetic_dataset

class TestSyntheticGenerator:
    
    def test_raises_on_missing_reductions(self, monkeypatch):
        """Test that ConfigurationError is raised if REDUCTION_LEVELS is missing and no default exists."""
        # Simulate a scenario where get_reductions would fail
        # We monkeypatch get_reductions to raise the error
        from data import generate_synthetic
        
        def mock_get_reductions():
            raise ConfigurationError("Reduction levels missing.")
        
        monkeypatch.setattr(generate_synthetic, "get_reductions", mock_get_reductions)
        
        with pytest.raises(ConfigurationError, match="Reduction levels missing"):
            generate_synthetic_dataset(materials=["Al"], output_dir=Path("/tmp/test"))

    def test_generates_expected_columns(self, tmp_path):
        """Test that the generated dataframe has the correct columns."""
        output_dir = tmp_path
        generate_synthetic_dataset(materials=["Al"], output_dir=output_dir)
        
        output_file = output_dir / "synthetic_ebsd_fallback.parquet"
        assert output_file.exists()
        
        df = pd.read_parquet(output_file)
        
        expected_columns = [
            "sample_id", "material", "reduction", "phi1", "Phi", "phi2",
            "confidence_index", "grain_id", "is_synthetic"
        ]
        
        for col in expected_columns:
            assert col in df.columns, f"Missing column: {col}"

    def test_reductions_match_config(self, tmp_path):
        """Test that the reduction values in the data match the config."""
        # Set a specific reduction list in env to ensure consistency
        os.environ["REDUCTION_LEVELS"] = "30,60"
        
        # Force reload of config to pick up env var (if using cached import)
        # In a real test suite, we might need to reload the module
        from config import get_reductions
        expected_reductions = get_reductions()
        
        output_dir = tmp_path
        generate_synthetic_dataset(materials=["Al"], output_dir=output_dir)
        
        df = pd.read_parquet(output_dir / "synthetic_ebsd_fallback.parquet")
        
        unique_reductions = sorted(df["reduction"].unique().tolist())
        assert unique_reductions == expected_reductions, f"Expected {expected_reductions}, got {unique_reductions}"

    def test_materials_included(self, tmp_path):
        """Test that all requested materials are present in the output."""
        materials = ["Al", "Cu"]
        output_dir = tmp_path
        generate_synthetic_dataset(materials=materials, output_dir=output_dir)
        
        df = pd.read_parquet(output_dir / "synthetic_ebsd_fallback.parquet")
        
        assert set(df["material"].unique()) == set(materials)

    def test_confidence_range(self, tmp_path):
        """Test that confidence indices are within valid bounds."""
        output_dir = tmp_path
        generate_synthetic_dataset(materials=["Al"], output_dir=output_dir)
        
        df = pd.read_parquet(output_dir / "synthetic_ebsd_fallback.parquet")
        
        assert df["confidence_index"].min() >= 0.0
        assert df["confidence_index"].max() <= 1.0
        assert (df["confidence_index"] >= 0.05).all() # Based on generation logic