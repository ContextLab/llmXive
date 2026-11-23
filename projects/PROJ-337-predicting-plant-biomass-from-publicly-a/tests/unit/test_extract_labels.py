"""
Unit tests for the ground-truth extraction script.
"""

import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.extract_labels import (
    load_preprocessed_data,
    extract_biomass_labels,
    calculate_exclusion_rate,
    dynamic_site_subsampling,
    save_extracted_labels,
)


class TestLoadPreprocessedData:
    def test_load_single_csv(self, tmp_path):
        """Test loading a single CSV file."""
        # Create a test CSV file
        csv_file = tmp_path / "test.csv"
        df_test = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        df_test.to_csv(csv_file, index=False)

        # Load the data
        result = load_preprocessed_data(tmp_path)

        # Verify the result
        assert len(result) == 3
        assert "a" in result.columns
        assert "b" in result.columns
        assert "source_file" in result.columns
        assert result["source_file"].iloc[0] == "test.csv"

    def test_load_multiple_csvs(self, tmp_path):
        """Test loading multiple CSV files."""
        # Create test CSV files
        df1 = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        df2 = pd.DataFrame({"a": [5, 6], "b": [7, 8]})
        df1.to_csv(tmp_path / "test1.csv", index=False)
        df2.to_csv(tmp_path / "test2.csv", index=False)

        # Load the data
        result = load_preprocessed_data(tmp_path)

        # Verify the result
        assert len(result) == 4
        assert result["source_file"].nunique() == 2

    def test_no_csv_files(self, tmp_path):
        """Test loading when no CSV files are present."""
        with pytest.raises(FileNotFoundError):
            load_preprocessed_data(tmp_path)


class TestExtractBiomassLabels:
    def test_extract_valid_labels(self):
        """Test extracting valid biomass labels."""
        df = pd.DataFrame({
            "site_id": ["A", "B", "C", "D"],
            "biomass_label": [10.0, 20.0, None, 30.0],
        })

        result, sites = extract_biomass_labels(df)

        assert len(result) == 3
        assert None not in result["biomass_label"].values
        assert set(sites) == {"A", "B", "D"}

    def test_missing_label_column(self):
        """Test extraction when label column is missing."""
        df = pd.DataFrame({
            "site_id": ["A", "B", "C"],
            "other_column": [1, 2, 3],
        })

        with pytest.raises(ValueError):
            extract_biomass_labels(df, label_column="biomass_label")

    def test_missing_site_column(self):
        """Test extraction when site column is missing."""
        df = pd.DataFrame({
            "biomass_label": [10.0, 20.0, 30.0],
        })

        with pytest.raises(ValueError):
            extract_biomass_labels(df, site_column="site_id")


class TestCalculateExclusionRate:
    def test_normal_case(self):
        """Test exclusion rate calculation."""
        rate = calculate_exclusion_rate(100, 5)
        assert rate == 0.05

    def test_zero_total(self):
        """Test exclusion rate with zero total samples."""
        rate = calculate_exclusion_rate(0, 5)
        assert rate == 0.0

    def test_zero_excluded(self):
        """Test exclusion rate with zero excluded samples."""
        rate = calculate_exclusion_rate(100, 0)
        assert rate == 0.0


class TestDynamicSiteSubsampling:
    def test_subsampling_within_threshold(self):
        """Test subsampling when exclusion rate is already within threshold."""
        # Create a dataset with 10 sites, each with 10 samples
        # All sites have >= min_samples_per_site, so exclusion rate is 0
        df = pd.DataFrame({
            "site_id": [f"site_{i}" for i in range(10) for _ in range(10)],
            "biomass_label": list(range(100)),
        })

        sites = df["site_id"].unique()

        result, metadata = dynamic_site_subsampling(
            df,
            sites,
            max_exclusion_rate=0.05,
            min_samples_per_site=5,
        )

        assert metadata["final_exclusion_rate"] == 0.0
        assert metadata["reason"] == "success"
        assert len(result) == 100

    def test_subsampling_removes_sites(self):
        """Test subsampling when some sites need to be removed."""
        # Create a dataset with 5 sites:
        # - 3 sites with 10 samples each (valid)
        # - 2 sites with 2 samples each (invalid, < min_samples_per_site)
        df = pd.DataFrame({
            "site_id": (
                [f"valid_{i}" for i in range(3) for _ in range(10)] +
                [f"invalid_{i}" for i in range(2) for _ in range(2)]
            ),
            "biomass_label": list(range(34)),
        })

        sites = df["site_id"].unique()
        total_samples = len(df)

        result, metadata = dynamic_site_subsampling(
            df,
            sites,
            max_exclusion_rate=0.05,
            min_samples_per_site=5,
        )

        # The exclusion rate should be the proportion of samples from invalid sites
        # (4 samples out of 34 = 11.76%)
        # Since this is > 5%, the algorithm should remove sites until the
        # exclusion rate is <= 5%.
        # However, removing a site increases the exclusion rate, so the algorithm
        # should remove the sites with the fewest samples first.
        # In this case, the invalid sites have the fewest samples, so they are
        # already excluded. The algorithm should then remove the valid sites
        # with the fewest samples (all have 10 samples) until the exclusion rate
        # is <= 5%.

        # Let's calculate the expected result:
        # - Initial exclusion rate: 4/34 = 11.76%
        # - Remove one valid site (10 samples): exclusion rate = (4 + 10) / 34 = 41.18%
        # - This is worse, so the algorithm should stop and report failure.

        # Actually, I think the algorithm is designed to remove sites to reduce
        # the exclusion rate. But in this case, removing sites increases the
        # exclusion rate. So the algorithm should report failure.

        assert metadata["final_exclusion_rate"] > 0.05
        assert "Could not achieve exclusion rate" in metadata["reason"]

    def test_subsampling_with_iterations(self):
        """Test subsampling with multiple iterations."""
        # Create a dataset with 20 sites:
        # - 10 sites with 10 samples each (valid)
        # - 10 sites with 1 sample each (invalid, < min_samples_per_site)
        df = pd.DataFrame({
            "site_id": (
                [f"valid_{i}" for i in range(10) for _ in range(10)] +
                [f"invalid_{i}" for i in range(10) for _ in range(1)]
            ),
            "biomass_label": list(range(110)),
        })

        sites = df["site_id"].unique()

        result, metadata = dynamic_site_subsampling(
            df,
            sites,
            max_exclusion_rate=0.05,
            min_samples_per_site=5,
            max_iterations=5,
        )

        assert metadata["iterations"] <= 5
        assert "sites_removed" in metadata

    def test_random_seed_reproducibility(self):
        """Test that the same random seed produces the same result."""
        df = pd.DataFrame({
            "site_id": [f"site_{i}" for i in range(10) for _ in range(10)],
            "biomass_label": list(range(100)),
        })
        sites = df["site_id"].unique()

        result1, metadata1 = dynamic_site_subsampling(
            df,
            sites,
            random_seed=42,
        )

        result2, metadata2 = dynamic_site_subsampling(
            df,
            sites,
            random_seed=42,
        )

        assert len(result1) == len(result2)
        assert metadata1["final_exclusion_rate"] == metadata2["final_exclusion_rate"]


class TestSaveExtractedLabels:
    def test_save_csv_and_metadata(self, tmp_path):
        """Test saving CSV and metadata files."""
        df = pd.DataFrame({
            "site_id": ["A", "B", "C"],
            "biomass_label": [10.0, 20.0, 30.0],
        })

        output_path = tmp_path / "extracted_labels.csv"
        metadata = {
            "total_initial_samples": 3,
            "total_sites": 3,
            "iterations": 0,
            "sites_removed": [],
            "final_exclusion_rate": 0.0,
            "reason": "success",
        }

        save_extracted_labels(df, output_path, metadata)

        # Verify CSV file
        assert output_path.exists()
        result_df = pd.read_csv(output_path)
        assert len(result_df) == 3
        assert "site_id" in result_df.columns
        assert "biomass_label" in result_df.columns

        # Verify metadata file
        metadata_path = output_path.with_suffix(".json")
        assert metadata_path.exists()
        with open(metadata_path) as f:
            loaded_metadata = json.load(f)
        assert loaded_metadata["final_exclusion_rate"] == 0.0
        assert "output_checksum" in loaded_metadata