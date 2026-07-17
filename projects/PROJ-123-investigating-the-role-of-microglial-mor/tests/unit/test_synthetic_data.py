"""
Unit tests for the synthetic data generator (T007).

Verifies that the generated data conforms to the schema defined in T006a
and contains plausible values for the specified metrics.
"""

import os
import json
import tempfile
import pytest
import pandas as pd
import numpy as np

from code.synthetic_data import (
    generate_microglia_cell,
    generate_ground_truth_metrics,
    generate_synthetic_dataset,
    set_seed
)
from code.config import get_path


class TestSyntheticDataGeneration:
    """Tests for the core generation functions."""

    def test_generate_microglia_cell_structure(self):
        """Test that a single generated cell has the required structure."""
        cell = generate_microglia_cell("Hippocampus", "Normal", seed=123)

        assert "subject_id" in cell
        assert "brain_region" in cell
        assert "pathology_status" in cell
        assert "morphological_metrics" in cell
        assert "cognitive_score" in cell

        metrics = cell["morphological_metrics"]
        assert "branch_points" in metrics
        assert "total_length" in metrics
        assert "soma_area" in metrics
        assert "sholl_intersections" in metrics

        # Verify types
        assert isinstance(cell["brain_region"], str)
        assert isinstance(cell["cognitive_score"], float)
        assert isinstance(metrics["branch_points"], int)
        assert isinstance(metrics["total_length"], float)

    def test_generate_microglia_cell_enum_values(self):
        """Test that enum fields only contain allowed values."""
        regions = ["Hippocampus", "Prefrontal Cortex"]
        statuses = ["Normal", "Early AD"]

        for region in regions:
            for status in statuses:
                cell = generate_microglia_cell(region, status, seed=42)
                assert cell["brain_region"] == region
                assert cell["pathology_status"] == status

    def test_generate_microglia_cell_plausible_ranges(self):
        """Test that generated values are within plausible biological ranges."""
        cell = generate_microglia_cell("Hippocampus", "Normal", seed=999)
        metrics = cell["morphological_metrics"]

        # Branch points: 5-60
        assert 5 <= metrics["branch_points"] <= 60

        # Total length: 50-800 microns
        assert 50 <= metrics["total_length"] <= 800

        # Soma area: 30-400 microns^2
        assert 30 <= metrics["soma_area"] <= 400

        # Sholl intersections: 2-40
        assert 2 <= metrics["sholl_intersections"] <= 40

        # Cognitive score: 10-180 seconds
        assert 10 <= cell["cognitive_score"] <= 180

    def test_generate_ground_truth_metrics_count(self):
        """Test that the correct number of cells is generated."""
        n = 50
        cells = generate_ground_truth_metrics(n_cells=n, seed=42)
        assert len(cells) == n

    def test_generate_synthetic_dataset_creates_file(self):
        """Test that the dataset generation creates the expected files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "test_synthetic.csv")
            result_path = generate_synthetic_dataset(output_path=csv_path, n_cells=10, seed=42)

            assert os.path.exists(result_path)
            assert result_path == csv_path

            # Check JSON ground truth also created
            json_path = csv_path.replace(".csv", "_ground_truth.json")
            assert os.path.exists(json_path)

    def test_synthetic_dataset_schema_compliance(self):
        """Test that the generated CSV matches the T006a schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "schema_test.csv")
            generate_synthetic_dataset(output_path=csv_path, n_cells=20, seed=42)

            df = pd.read_csv(csv_path)

            # Required columns from T006a
            required_cols = [
                "subject_id", "brain_region", "pathology_status",
                "branch_points", "total_length", "soma_area",
                "sholl_intersections", "cognitive_score"
            ]

            for col in required_cols:
                assert col in df.columns, f"Missing column: {col}"

            # Check for forbidden columns (scope creep prevention)
            forbidden_cols = ["fractal_dimension", "complexity_index"]
            for col in forbidden_cols:
                assert col not in df.columns, f"Forbidden column found: {col}"

            # Check data types
            assert df["branch_points"].dtype in [np.int64, np.int32, np.float64] # int or float is ok
            assert df["total_length"].dtype in [np.float64, np.float32]
            assert df["soma_area"].dtype in [np.float64, np.float32]

    def test_synthetic_data_reproducibility(self):
        """Test that generating data with the same seed produces identical results."""
        set_seed(12345)
        cells1 = generate_ground_truth_metrics(n_cells=5, seed=12345)

        set_seed(12345)
        cells2 = generate_ground_truth_metrics(n_cells=5, seed=12345)

        # Compare specific values
        assert cells1[0]["morphological_metrics"]["branch_points"] == cells2[0]["morphological_metrics"]["branch_points"]
        assert cells1[0]["cognitive_score"] == cells2[0]["cognitive_score"]

    def test_pathology_effect_on_metrics(self):
        """
        Test that 'Early AD' status results in lower complexity metrics
        compared to 'Normal' status, reflecting the biological hypothesis.
        """
        # Generate a batch of Normal cells
        normal_cells = generate_ground_truth_metrics(n_cells=100, seed=1)
        # Filter for Normal status (ensure we have some)
        normal_subset = [c for c in normal_cells if c["pathology_status"] == "Normal"]
        
        # Generate a batch of AD cells
        ad_cells = generate_ground_truth_metrics(n_cells=100, seed=2)
        ad_subset = [c for c in ad_cells if c["pathology_status"] == "Early AD"]

        if not normal_subset or not ad_subset:
            pytest.skip("Could not generate sufficient samples for comparison")

        avg_branch_normal = np.mean([c["morphological_metrics"]["branch_points"] for c in normal_subset])
        avg_branch_ad = np.mean([c["morphological_metrics"]["branch_points"] for c in ad_subset])

        # AD should generally have fewer branch points
        assert avg_branch_ad < avg_branch_normal, "AD cells should have fewer branch points than Normal cells"

        avg_cognitive_normal = np.mean([c["cognitive_score"] for c in normal_subset])
        avg_cognitive_ad = np.mean([c["cognitive_score"] for c in ad_subset])

        # AD should have higher latency (worse performance)
        assert avg_cognitive_ad > avg_cognitive_normal, "AD cells should correspond to higher cognitive latency"
