"""
Tests for user susceptibility score computation.

Validates the proxy susceptibility score formula:
(historical_degree >= 2 AND historical_shares >= 1) ? 1.0 : 0.0
"""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from pipeline.user_susceptibility import compute_susceptibility_score, compute_susceptibility_scores


class TestComputeSusceptibilityScore:
    """Unit tests for the susceptibility score formula."""

    def test_high_degree_and_shares_returns_one(self):
        """Score is 1.0 when both thresholds are met."""
        row = pd.Series({"historical_degree": 2, "historical_shares": 1})
        assert compute_susceptibility_score(row) == 1.0

    def test_high_degree_low_shares_returns_zero(self):
        """Score is 0.0 when degree meets threshold but shares does not."""
        row = pd.Series({"historical_degree": 3, "historical_shares": 0})
        assert compute_susceptibility_score(row) == 0.0

    def test_low_degree_high_shares_returns_zero(self):
        """Score is 0.0 when shares meets threshold but degree does not."""
        row = pd.Series({"historical_degree": 1, "historical_shares": 5})
        assert compute_susceptibility_score(row) == 0.0

    def test_low_degree_and_shares_returns_zero(self):
        """Score is 0.0 when neither threshold is met."""
        row = pd.Series({"historical_degree": 0, "historical_shares": 0})
        assert compute_susceptibility_score(row) == 0.0

    def test_boundary_degree_exactly_two(self):
        """Degree of exactly 2 meets the threshold."""
        row = pd.Series({"historical_degree": 2, "historical_shares": 1})
        assert compute_susceptibility_score(row) == 1.0

    def test_boundary_degree_below_two(self):
        """Degree of 1 does not meet the threshold."""
        row = pd.Series({"historical_degree": 1, "historical_shares": 1})
        assert compute_susceptibility_score(row) == 0.0

    def test_boundary_shares_exactly_one(self):
        """Shares of exactly 1 meets the threshold."""
        row = pd.Series({"historical_degree": 2, "historical_shares": 1})
        assert compute_susceptibility_score(row) == 1.0

    def test_boundary_shares_below_one(self):
        """Shares of 0 does not meet the threshold."""
        row = pd.Series({"historical_degree": 2, "historical_shares": 0})
        assert compute_susceptibility_score(row) == 0.0

    def test_high_values_return_one(self):
        """High values for both metrics return 1.0."""
        row = pd.Series({"historical_degree": 10, "historical_shares": 5})
        assert compute_susceptibility_score(row) == 1.0

    def test_missing_columns_defaults_to_zero(self):
        """Missing columns default to 0, resulting in score of 0.0."""
        row = pd.Series({"other_column": 1})
        assert compute_susceptibility_score(row) == 0.0


class TestComputeSusceptibilityScores:
    """Integration tests for the full computation pipeline."""

    def test_full_pipeline_writes_output(self):
        """Full pipeline reads input and writes output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"

            # Create test input
            df_input = pd.DataFrame({
                "historical_degree": [0, 1, 2, 3],
                "historical_shares": [0, 1, 0, 1],
            })
            df_input.to_csv(input_path, index=False)

            # Run computation
            result_path = compute_susceptibility_scores(
                input_path=str(input_path),
                output_path=str(output_path),
                seed=12345,
            )

            # Verify output exists
            assert result_path.exists()

            # Verify output content
            df_output = pd.read_csv(output_path)
            assert "susceptibility_score" in df_output.columns
            assert len(df_output) == 4

    def test_output_scores_match_formula(self):
        """Output susceptibility scores match the expected formula."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"

            # Create test input with known expected outputs
            df_input = pd.DataFrame({
                "historical_degree": [0, 1, 2, 2, 3],
                "historical_shares": [0, 0, 0, 1, 1],
            })
            df_input.to_csv(input_path, index=False)

            # Run computation
            compute_susceptibility_scores(
                input_path=str(input_path),
                output_path=str(output_path),
                seed=12345,
            )

            # Verify output
            df_output = pd.read_csv(output_path)
            expected_scores = [0.0, 0.0, 0.0, 1.0, 1.0]
            assert df_output["susceptibility_score"].tolist() == expected_scores

    def test_missing_required_columns_raises_error(self):
        """Pipeline raises error when required columns are missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"

            # Create test input missing required columns
            df_input = pd.DataFrame({
                "other_column": [1, 2, 3],
            })
            df_input.to_csv(input_path, index=False)

            # Should raise ValueError
            with pytest.raises(ValueError, match="Missing required columns"):
                compute_susceptibility_scores(
                    input_path=str(input_path),
                    output_path=str(output_path),
                    seed=12345,
                )

    def test_large_dataset_computation(self):
        """Pipeline handles larger datasets correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"

            # Create larger test dataset
            df_input = pd.DataFrame({
                "historical_degree": list(range(100)),
                "historical_shares": list(range(100)),
            })
            df_input.to_csv(input_path, index=False)

            # Run computation
            compute_susceptibility_scores(
                input_path=str(input_path),
                output_path=str(output_path),
                seed=12345,
            )

            # Verify output
            df_output = pd.read_csv(output_path)
            assert len(df_output) == 100
            assert df_output["susceptibility_score"].sum() == 98  # degrees 2-99 with shares >= 1
