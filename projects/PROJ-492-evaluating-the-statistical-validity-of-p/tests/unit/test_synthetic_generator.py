"""
Unit tests for the synthetic dataset generator.
Verifies that the generator produces valid records and meets the count requirements.
"""

import json
import os
import tempfile
import csv
from pathlib import Path

import pytest
import numpy as np

from code.src.audit.synthetic import generate_synthetic_dataset, _generate_binary_summary, _generate_continuous_summary
from code.src.config import SEED


class TestSyntheticGenerator:
    """Tests for synthetic.py"""

    def test_binary_summary_generation(self):
        """Test that binary summary generation produces valid data."""
        summary, truth = _generate_binary_summary(inconsistent=False)

        assert "n_control" in summary
        assert "n_treatment" in summary
        assert "baseline_rate" in summary
        assert "treatment_rate" in summary
        assert "reported_p_value" in summary

        assert summary["n_control"] > 0
        assert summary["n_treatment"] > 0
        assert 0 < summary["baseline_rate"] < 1
        assert 0 < summary["treatment_rate"] < 1
        assert 0 <= summary["reported_p_value"] <= 1

        assert "true_p_value" in truth
        assert truth["is_inconsistent"] is False

    def test_continuous_summary_generation(self):
        """Test that continuous summary generation produces valid data."""
        summary, truth = _generate_continuous_summary(inconsistent=False)

        assert "n_control" in summary
        assert "n_treatment" in summary
        assert "std_control" in summary
        assert "std_treatment" in summary

        assert summary["n_control"] > 0
        assert summary["n_treatment"] > 0
        assert summary["std_control"] > 0
        assert summary["std_treatment"] > 0

    def test_inconsistent_generation(self):
        """Test that inconsistent flag actually introduces discrepancies."""
        # Run multiple times to ensure we hit the inconsistent branch
        inconsistencies_found = 0
        for _ in range(20):
            summary, truth = _generate_binary_summary(inconsistent=True)
            if truth["is_inconsistent"]:
                inconsistencies_found += 1

        # Should find inconsistencies most of the time given the logic
        assert inconsistencies_found > 10, "Inconsistent generation logic may be broken"

    def test_full_dataset_generation_count(self):
        """Test that the full dataset generator creates the required number of records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            summaries_path, gt_path = generate_synthetic_dataset(
                output_dir=tmpdir,
                num_records=10000,
                seed=SEED
            )

            # Verify file existence
            assert summaries_path.exists(), "Summaries file not created"
            assert gt_path.exists(), "Ground truth file not created"

            # Verify record count
            with open(summaries_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 10000, f"Expected 10000 records, got {len(rows)}"

            with open(gt_path, 'r', encoding='utf-8') as f:
                gts = json.load(f)
                assert len(gts) == 10000, f"Expected 10000 ground truths, got {len(gts)}"

    def test_dataset_variety(self):
        """Test that the generated dataset contains both binary and continuous outcomes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            summaries_path, _ = generate_synthetic_dataset(
                output_dir=tmpdir,
                num_records=1000,
                seed=SEED
            )

            with open(summaries_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            test_types = [r["test_type"] for r in rows]
            assert "binary" in test_types, "No binary outcomes generated"
            assert "continuous" in test_types, "No continuous outcomes generated"

    def test_determinism(self):
        """Test that generation is deterministic with the same seed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate twice
            p1, _ = generate_synthetic_dataset(tmpdir, num_records=100, seed=42)
            
            # Read first result
            with open(p1, 'r') as f:
                content1 = f.read()

            # Generate again
            p2, _ = generate_synthetic_dataset(tmpdir, num_records=100, seed=42)
            
            # Read second result
            with open(p2, 'r') as f:
                content2 = f.read()

            assert content1 == content2, "Generation is not deterministic with same seed"
