"""
Unit tests for p-value collection logic (T021).
"""
import pytest
import json
import os
import tempfile
from pathlib import Path

from utils.exceptions import HypothesisTestError
from collect_pvalues import collect_pvalues, aggregate_pvalues


class TestCollectPvalues:
    """Tests for the collect_pvalues function."""

    def test_correct_count(self, tmp_path):
        """Test that valid p-values are collected successfully."""
        p = 10
        pvalues = [0.5] * p
        output_dir = str(tmp_path)

        record = collect_pvalues(
            pvalues=pvalues,
            n_features=p,
            iteration=1,
            seed=42,
            output_dir=output_dir,
            rho=0.0,
            n=100,
            p=p,
            distribution_type="normal"
        )

        assert record["count"] == p
        assert record["pvalues"] == pvalues
        assert record["iteration"] == 1
        assert "sha256_pvalues" in record

        # Verify file was written
        traj_dir = Path(output_dir) / "trajectories"
        files = list(traj_dir.glob("*.json"))
        assert len(files) == 1

    def test_invalid_count_raises_error(self, tmp_path):
        """Test that mismatched count raises HypothesisTestError (FR-003)."""
        p = 10
        pvalues = [0.5] * 9  # One short
        output_dir = str(tmp_path)

        with pytest.raises(HypothesisTestError) as exc_info:
            collect_pvalues(
                pvalues=pvalues,
                n_features=p,
                iteration=1,
                seed=42,
                output_dir=output_dir,
                rho=0.0,
                n=100,
                p=p,
                distribution_type="normal"
            )

        assert "FR-003 Violation" in str(exc_info.value)

    def test_empty_pvalues_raises_error(self, tmp_path):
        """Test that empty list raises error when p > 0."""
        p = 5
        output_dir = str(tmp_path)

        with pytest.raises(HypothesisTestError):
            collect_pvalues(
                pvalues=[],
                n_features=p,
                iteration=1,
                seed=42,
                output_dir=output_dir,
                rho=0.0,
                n=100,
                p=p,
                distribution_type="normal"
            )

class TestAggregatePvalues:
    """Tests for the aggregate_pvalues function."""

    def test_aggregation(self, tmp_path):
        """Test that multiple records are aggregated correctly."""
        output_path = str(tmp_path / "aggregated.json")
        
        records = [
            {
                "pvalues": [0.1, 0.2],
                "seed": 1,
                "rho": 0.0,
                "n": 10,
                "p": 2,
                "count": 2
            },
            {
                "pvalues": [0.3, 0.4],
                "seed": 2,
                "rho": 0.1,
                "n": 20,
                "p": 2,
                "count": 2
            }
        ]

        aggregate_pvalues(records, output_path)

        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            data = json.load(f)

        assert data["total_pvalues"] == 4
        assert data["total_iterations"] == 2
        assert data["pvalues"] == [0.1, 0.2, 0.3, 0.4]
        assert len(data["metadata"]) == 2