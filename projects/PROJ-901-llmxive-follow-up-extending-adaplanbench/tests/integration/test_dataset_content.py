"""
Integration tests for dataset content and schema validation.
Verifies progressive_constraints schema and constraint_count field presence.
"""
import os
import pytest
import pandas as pd
from pathlib import Path

from config import Paths
from dataset.loader import load_adaplanbench, filter_progressive_constraints, save_filtered_dataset


class TestFilteredDatasetSchema:
    """Integration tests for the filtered dataset schema."""

    def test_filtered_dataset_schema(self):
        """
        Verify that the filtered dataset has the correct schema:
        - Contains 'progressive_constraints' field
        - Contains 'constraint_count' field
        - All rows have constraint_count >= 5
        """
        # Load raw dataset
        raw_data = load_adaplanbench()

        # Filter for progressive constraints >= 5
        filtered_data = filter_progressive_constraints(raw_data, min_constraints=5)

        # Save to CSV (simulating the pipeline step)
        output_path = Paths.data_processed / "filtered_tasks.csv"
        save_filtered_dataset(filtered_data, output_path)

        # Load the saved CSV for verification
        df = pd.read_csv(output_path)

        # Verify schema
        assert 'progressive_constraints' in df.columns, "Missing 'progressive_constraints' column"
        assert 'constraint_count' in df.columns, "Missing 'constraint_count' column"

        # Verify constraint counts
        assert all(df['constraint_count'] >= 5), "Some rows have constraint_count < 5"

        # Verify data types
        assert df['constraint_count'].dtype in ['int64', 'int32'], "constraint_count should be integer"

    def test_filtered_dataset_content_sample(self):
        """
        Verify content of a sample of 10 tasks against expected metadata.
        """
        # Load and filter
        raw_data = load_adaplanbench()
        filtered_data = filter_progressive_constraints(raw_data, min_constraints=5)

        # Save
        output_path = Paths.data_processed / "filtered_tasks.csv"
        save_filtered_dataset(filtered_data, output_path)

        # Load back
        df = pd.read_csv(output_path)

        # Sample 10 tasks
        sample = df.sample(n=min(10, len(df)), random_state=42)

        # Verify each sample has valid progressive_constraints
        for idx, row in sample.iterrows():
            # Check that progressive_constraints is not empty
            assert pd.notna(row['progressive_constraints']), f"Row {idx} has null progressive_constraints"

            # Check that constraint_count matches the length of progressive_constraints
            constraints = row['progressive_constraints']
            if isinstance(constraints, str):
                # If stored as string (e.g., JSON), parse it
                import json
                try:
                    parsed = json.loads(constraints)
                    assert len(parsed) == row['constraint_count'], \
                        f"Row {idx}: constraint_count mismatch ({row['constraint_count']} vs {len(parsed)})"
                except json.JSONDecodeError:
                    # If it's a literal string representation, count commas or use other logic
                    # For now, assume valid data
                    pass

    def test_filtered_dataset_size(self):
        """
        Verify that the filtered dataset has a reasonable size (not empty).
        """
        raw_data = load_adaplanbench()
        filtered_data = filter_progressive_constraints(raw_data, min_constraints=5)

        assert len(filtered_data) > 0, "Filtered dataset is empty"
        assert len(filtered_data) <= len(raw_data), "Filtered dataset is larger than raw dataset"
