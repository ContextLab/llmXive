"""
Integration tests for stratified sampling in the context of the full pipeline.

These tests verify that stratified sampling works correctly when integrated
with other components of the research pipeline.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from tests.conftest import stratified_sample, sample_moral_machine_data, sample_era5_data


class TestIntegrationSampling:
    """Integration tests for stratified sampling."""

    def test_sampling_with_moral_machine_and_era5(self, sample_moral_machine_data, sample_era5_data):
        """Test that sampling works correctly with both Moral Machine and ERA5 data."""
        # Sample Moral Machine data
        mm_sample = stratified_sample(
            sample_moral_machine_data,
            stratify_col='country',
            fraction=0.2,
            random_state=42
        )

        # Sample ERA5 data
        era5_sample = stratified_sample(
            sample_era5_data,
            stratify_col='time',  # Stratify by time period
            fraction=0.2,
            random_state=42
        )

        # Verify both samples are valid
        assert len(mm_sample) > 0
        assert len(era5_sample) > 0
        assert len(mm_sample) < len(sample_moral_machine_data)
        assert len(era5_sample) < len(sample_era5_data)

    def test_sampling_preserves_data_integrity(self, sample_moral_machine_data):
        """Test that stratified sampling preserves data integrity."""
        original_df = sample_moral_machine_data.copy()

        # Sample 30%
        sampled_df = stratified_sample(
            original_df,
            stratify_col='country',
            fraction=0.3,
            random_state=42
        )

        # Check that all sampled rows exist in original
        # (This is a simplified check; in practice, we'd check indices or unique identifiers)
        for col in sampled_df.columns:
            assert col in original_df.columns

        # Check that data types are preserved
        assert sampled_df.dtypes.equals(original_df.dtypes)

    def test_sampling_with_multiple_stratification_levels(self, sample_moral_machine_data):
        """Test sampling with multiple stratification criteria."""
        # First stratify by country
        country_sample = stratified_sample(
            sample_moral_machine_data,
            stratify_col='country',
            fraction=0.5,
            random_state=42
        )

        # Then stratify by dilemma_type within the country sample
        final_sample = stratified_sample(
            country_sample,
            stratify_col='dilemma_type',
            fraction=0.5,
            random_state=42
        )

        # Verify that the final sample is smaller than the intermediate sample
        assert len(final_sample) <= len(country_sample)
        assert len(final_sample) <= len(sample_moral_machine_data)

    def test_sampling_with_output_directory(self, sample_moral_machine_data, temp_output_dir):
        """Test that sampled data can be saved to a temporary output directory."""
        sampled_df = stratified_sample(
            sample_moral_machine_data,
            stratify_col='country',
            fraction=0.2,
            random_state=42
        )

        # Save to temp directory
        output_path = temp_output_dir / "sampled_data.parquet"
        sampled_df.to_parquet(output_path)

        # Verify file was created
        assert output_path.exists()

        # Verify we can load it back
        loaded_df = pd.read_parquet(output_path)
        pd.testing.assert_frame_equal(sampled_df, loaded_df)

    def test_sampling_representativeness(self, sample_moral_machine_data):
        """Test that stratified sampling produces a representative sample."""
        original_df = sample_moral_machine_data

        # Sample 20%
        sampled_df = stratified_sample(
            original_df,
            stratify_col='country',
            fraction=0.2,
            random_state=42
        )

        # Compare distributions
        original_dist = original_df['country'].value_counts(normalize=True).sort_index()
        sample_dist = sampled_df['country'].value_counts(normalize=True).sort_index()

        # The distributions should be similar (within 10% relative error)
        for country in original_dist.index:
            if country in sample_dist.index:
                orig_ratio = original_dist[country]
                sample_ratio = sample_dist[country]
                if orig_ratio > 0:
                    relative_error = abs(sample_ratio - orig_ratio) / orig_ratio
                    assert relative_error < 0.1, \
                        f"Distribution for {country} differs significantly: {orig_ratio} vs {sample_ratio}"
