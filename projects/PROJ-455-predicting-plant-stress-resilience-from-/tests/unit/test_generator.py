"""
Unit tests for the synthetic data generator.
"""

import os
import tempfile
import pytest
import pandas as pd
import numpy as np

from data.generator import generate_synthetic_data, generate_lodo_synthetic_datasets
from data.models import StressType


class TestSyntheticGenerator:
    """Tests for the synthetic data generation functionality."""

    def test_generate_valid_stress_types(self):
        """Test generation for all valid stress types."""
        for stress_type in StressType:
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, f"test_{stress_type.value}.parquet")
                result_path = generate_synthetic_data(
                    n_samples=10,
                    stress_type=stress_type.value,
                    output_path=output_path
                )

                assert os.path.exists(result_path)
                df = pd.read_parquet(result_path)
                assert len(df) == 10
                assert df["stress_type"].iloc[0] == stress_type.value

    def test_invalid_stress_type_raises_error(self):
        """Test that invalid stress type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid stress_type"):
            generate_synthetic_data(
                n_samples=10,
                stress_type="INVALID_STRESS",
                output_path="dummy.parquet"
            )

    def test_sample_count(self):
        """Test that the correct number of samples is generated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_count.parquet")
            result_path = generate_synthetic_data(
                n_samples=50,
                stress_type="DROUGHT",
                output_path=output_path
            )

            df = pd.read_parquet(result_path)
            assert len(df) == 50

    def test_required_columns_present(self):
        """Test that all required columns are present in the output."""
        required_columns = [
            "sample_id", "stress_type", "stress_intensity",
            "biomass_recovery", "survival_rate", "recovery_days",
            "recovery_index"
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_cols.parquet")
            generate_synthetic_data(
                n_samples=10,
                stress_type="HEAT",
                output_path=output_path
            )

            df = pd.read_parquet(output_path)
            for col in required_columns:
                assert col in df.columns

    def test_recovery_metrics_range(self):
        """Test that recovery metrics are in valid ranges."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_range.parquet")
            generate_synthetic_data(
                n_samples=100,
                stress_type="SALT",
                output_path=output_path
            )

            df = pd.read_parquet(output_path)

            # Biomass recovery should be between 0 and 1
            assert df["biomass_recovery"].between(0.0, 1.0).all()
            # Survival rate should be between 0 and 1
            assert df["survival_rate"].between(0.0, 1.0).all()
            # Recovery days should be between 7 and 21
            assert df["recovery_days"].between(7, 21).all()
            # Stress intensity should be between 0.3 and 1.0
            assert df["stress_intensity"].between(0.3, 1.0).all()

    def test_pathway_metabolites_present(self):
        """Test that pathway-specific metabolites are present."""
        pathway_metabolites = [
            "Proline", "Glycine_Betaine", "ABA", "Jasmonic_Acid"
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_pathway.parquet")
            generate_synthetic_data(
                n_samples=10,
                stress_type="DROUGHT",
                output_path=output_path
            )

            df = pd.read_parquet(output_path)
            for metabolite in pathway_metabolites:
                assert metabolite in df.columns

    def test_lodo_dataset_generation(self):
        """Test LODO synthetic dataset generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            datasets = generate_lodo_synthetic_datasets(
                n_datasets=3,
                stress_types=["DROUGHT", "HEAT"],
                samples_per_dataset=50,
                base_path=tmpdir
            )

            assert len(datasets) == 3
            for path in datasets:
                assert os.path.exists(path)
                df = pd.read_parquet(path)
                assert len(df) >= 50  # Minimum sample size enforced

    def test_metabolite_values_positive(self):
        """Test that all metabolite values are non-negative."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_positive.parquet")
            generate_synthetic_data(
                n_samples=20,
                stress_type="COLD",
                output_path=output_path
            )

            df = pd.read_parquet(output_path)
            # Check that all numeric columns (except IDs and metrics) are positive
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if col not in ["stress_intensity", "recovery_days"]:
                    assert (df[col] >= 0).all()
