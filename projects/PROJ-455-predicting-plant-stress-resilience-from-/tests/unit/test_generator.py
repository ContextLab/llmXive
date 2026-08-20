"""
Unit tests for the Mechanism-Guided Synthetic Data Generator.
"""
import os
import tempfile
import pandas as pd
import pytest
from datetime import datetime

from code.data.generator import generate_synthetic_data, STRESS_MECHANISMS, ALL_METABOLITES
from code.data.models import StressType

class TestSyntheticGenerator:
    def test_generate_default_stress_distribution(self, tmp_path):
        """Test generation with default stress distribution."""
        output_file = tmp_path / "synthetic_test.parquet"
        result_path = generate_synthetic_data(n_samples=50, output_path=str(output_file))
        
        assert os.path.exists(result_path)
        df = pd.read_parquet(result_path)
        
        assert len(df) == 50
        assert "accession_id" in df.columns
        assert "stress_type" in df.columns
        assert "biomass_change" in df.columns
        
        # Check that multiple stress types are present
        unique_stresses = df["stress_type"].unique()
        assert len(unique_stresses) > 1

    def test_generate_single_stress_type(self, tmp_path):
        """Test generation with a specific stress type."""
        output_file = tmp_path / "synthetic_drought.parquet"
        result_path = generate_synthetic_data(n_samples=20, stress_type=StressType.DROUGHT, output_path=str(output_file))
        
        assert os.path.exists(result_path)
        df = pd.read_parquet(result_path)
        
        assert len(df) == 20
        assert all(df["stress_type"] == StressType.DROUGHT.value)

    def test_metabolite_columns_exist(self, tmp_path):
        """Test that expected metabolite columns are present."""
        output_file = tmp_path / "synthetic_met.parquet"
        generate_synthetic_data(n_samples=10, output_path=str(output_file))
        
        df = pd.read_parquet(output_file)
        
        # Check for a few known metabolites from the background list
        expected_cols = ["met_Glucose", "met_Fructose", "met_Sucrose"]
        for col in expected_cols:
            assert col in df.columns, f"Column {col} missing from dataframe"

    def test_ground_truth_mechanism_included(self, tmp_path):
        """Test that ground truth mechanism is included in metadata."""
        output_file = tmp_path / "synthetic_gt.parquet"
        generate_synthetic_data(n_samples=10, stress_type=StressType.HEAT, output_path=str(output_file))
        
        df = pd.read_parquet(output_file)
        
        assert "ground_truth_mechanism" in df.columns
        # Check that the mechanism for HEAT is present
        mechanisms = df.iloc[0]["ground_truth_mechanism"]
        assert "HSP70" in mechanisms
        assert "Glutathione" in mechanisms

    def test_signal_injection_logic(self, tmp_path):
        """
        Verify that mechanism-guided metabolites have higher values than background.
        This is a probabilistic check, so we run with a larger sample.
        """
        output_file = tmp_path / "synthetic_signal.parquet"
        generate_synthetic_data(n_samples=100, stress_type=StressType.DROUGHT, output_path=str(output_file))
        
        df = pd.read_parquet(output_file)
        
        drought_mechanism = STRESS_MECHANISMS[StressType.DROUGHT]
        # Get columns for mechanism metabolites
        mech_cols = [f"met_{m}" for m in drought_mechanism if f"met_{m}" in df.columns]
        
        if mech_cols:
            mean_mech = df[mech_cols].mean().mean()
            # Calculate mean of background metabolites (excluding mechanism ones)
            background_cols = [c for c in df.columns if c.startswith("met_") and c not in mech_cols]
            mean_bg = df[background_cols].mean().mean() if background_cols else 0
            
            # The mechanism metabolites should be significantly higher on average
            # due to the signal injection (1.5x to 3.0x)
            assert mean_mech > mean_bg, "Mechanism metabolites should be higher than background"

    def test_output_format_parquet(self, tmp_path):
        """Test that output is a valid Parquet file."""
        output_file = tmp_path / "synthetic_format.parquet"
        generate_synthetic_data(n_samples=5, output_path=str(output_file))
        
        # Should not raise an error
        df = pd.read_parquet(output_file)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5