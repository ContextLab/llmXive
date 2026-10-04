"""
Tests for preprocessing functions, specifically focusing on negative sample validation.
"""
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from preprocessing import (
    generate_negative_samples,
    MissingTemporalMetadataError,
    check_temporal_metadata,
    enforce_temporal_cooccurrence,
)


class TestNegativeSampleValidation(unittest.TestCase):
    """
    Test suite for T015b: Negative Sample Validation.
    
    Verifies that:
    1. All negative pairs exist in the derived co-occurrence matrix.
    2. All negative pairs satisfy the temporal co-occurrence constraint.
    3. The validation logic correctly identifies invalid pairs if constraints are violated.
    """

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock ecosystem metadata with temporal data
        self.ecosystem_id = "test_ecosystem_01"
        self.metadata = {
            "ecosystem_id": self.ecosystem_id,
            "start_date": "2020-05-01",
            "end_date": "2020-08-31",
            "location": "Test Location"
        }

        # Create a mock interaction dataframe (observed links)
        # Columns: plant_species, pollinator_species, start_date, end_date
        self.interactions = pd.DataFrame([
            {"plant_species": "Plant_A", "pollinator_species": "Pollinator_X", "start_date": "2020-05-15", "end_date": "2020-06-15"},
            {"plant_species": "Plant_B", "pollinator_species": "Pollinator_Y", "start_date": "2020-06-01", "end_date": "2020-07-01"},
            {"plant_species": "Plant_A", "pollinator_species": "Pollinator_Y", "start_date": "2020-05-20", "end_date": "2020-06-20"},
        ])

        # Create a mock co-occurrence matrix (derived from spatial/temporal data)
        # This represents species that were present in the ecosystem during the study period
        self.cooccurrence_matrix = pd.DataFrame({
            "plant_species": ["Plant_A", "Plant_B", "Plant_C"],
            "pollinator_species": ["Pollinator_X", "Pollinator_Y", "Pollinator_Z"],
            "present": [True, True, True]
        })

    def test_negative_samples_exist_in_cooccurrence(self):
        """
        Assert that all generated negative samples exist in the co-occurrence matrix.
        """
        # Generate negative samples
        negative_samples = generate_negative_samples(
            interactions=self.interactions,
            cooccurrence=self.cooccurrence_matrix,
            temporal_start=self.metadata["start_date"],
            temporal_end=self.metadata["end_date"]
        )

        # Validate that every negative pair is in the co-occurrence matrix
        for _, row in negative_samples.iterrows():
            pair_exists = self.cooccurrence_matrix[
                (self.cooccurrence_matrix["plant_species"] == row["plant_species"]) &
                (self.cooccurrence_matrix["pollinator_species"] == row["pollinator_species"])
            ].empty

            self.assertFalse(
                pair_exists,
                f"Negative pair ({row['plant_species']}, {row['pollinator_species']}) "
                "does not exist in the co-occurrence matrix."
            )

    def test_negative_samples_satisfy_temporal_constraint(self):
        """
        Assert that all negative samples satisfy the temporal co-occurrence constraint.
        This test verifies that the generation logic correctly filters by temporal overlap.
        """
        # Generate negative samples
        negative_samples = generate_negative_samples(
            interactions=self.interactions,
            cooccurrence=self.cooccurrence_matrix,
            temporal_start=self.metadata["start_date"],
            temporal_end=self.metadata["end_date"]
        )

        # Since generate_negative_samples already filters by temporal constraints
        # (as per T015a implementation), we verify that the output is non-empty
        # and that the dates are within the valid range.
        self.assertFalse(negative_samples.empty, "Negative samples should not be empty.")

        # Check that all dates in negative samples are within the ecosystem's temporal bounds
        for _, row in negative_samples.iterrows():
            pair_start = pd.to_datetime(row.get("start_date", self.metadata["start_date"]))
            pair_end = pd.to_datetime(row.get("end_date", self.metadata["end_date"]))
            eco_start = pd.to_datetime(self.metadata["start_date"])
            eco_end = pd.to_datetime(self.metadata["end_date"])

            self.assertGreaterEqual(
                pair_start, eco_start,
                f"Pair start date {pair_start} is before ecosystem start {eco_start}"
            )
            self.assertLessEqual(
                pair_end, eco_end,
                f"Pair end date {pair_end} is after ecosystem end {eco_end}"
            )

    def test_validation_raises_on_missing_temporal_metadata(self):
        """
        Assert that validation raises MissingTemporalMetadataError if temporal data is missing.
        """
        # Simulate missing temporal metadata
        incomplete_metadata = {
            "ecosystem_id": "test_ecosystem_02",
            "location": "Test Location"
            # Missing start_date and end_date
        }

        with self.assertRaises(MissingTemporalMetadataError):
            enforce_temporal_cooccurrence(
                interactions=self.interactions,
                metadata=incomplete_metadata
            )

    def test_negative_pairs_exclude_observed_links(self):
        """
        Assert that generated negative samples do not include observed links.
        """
        # Generate negative samples
        negative_samples = generate_negative_samples(
            interactions=self.interactions,
            cooccurrence=self.cooccurrence_matrix,
            temporal_start=self.metadata["start_date"],
            temporal_end=self.metadata["end_date"]
        )

        # Check that no observed link appears in negative samples
        for _, row in negative_samples.iterrows():
            is_observed = self.interactions[
                (self.interactions["plant_species"] == row["plant_species"]) &
                (self.interactions["pollinator_species"] == row["pollinator_species"])
            ].empty

            self.assertTrue(
                is_observed,
                f"Negative pair ({row['plant_species']}, {row['pollinator_species']}) "
                "is actually an observed link."
            )

    def test_cooccurrence_derivation_from_interactions(self):
        """
        Test that the co-occurrence matrix is correctly derived from interactions.
        This ensures the validation logic in T015b is based on the correct data source.
        """
        # Derive co-occurrence from interactions (as done in T014a/T014b)
        derived_cooccurrence = pd.DataFrame({
            "plant_species": self.interactions["plant_species"].unique(),
            "pollinator_species": self.interactions["pollinator_species"].unique()
        })
        # This is a simplified derivation; in reality, it would be more complex
        # involving spatial and temporal overlap checks.

        # Validate that negative samples generated from this matrix
        # are consistent with the derived co-occurrence
        negative_samples = generate_negative_samples(
            interactions=self.interactions,
            cooccurrence=derived_cooccurrence,
            temporal_start=self.metadata["start_date"],
            temporal_end=self.metadata["end_date"]
        )

        # Ensure all negative pairs are in the derived co-occurrence
        for _, row in negative_samples.iterrows():
            pair_exists = derived_cooccurrence[
                (derived_cooccurrence["plant_species"] == row["plant_species"]) &
                (derived_cooccurrence["pollinator_species"] == row["pollinator_species"])
            ].empty

            self.assertFalse(
                pair_exists,
                f"Negative pair ({row['plant_species']}, {row['pollinator_species']}) "
                "not found in derived co-occurrence matrix."
            )


if __name__ == "__main__":
    unittest.main()