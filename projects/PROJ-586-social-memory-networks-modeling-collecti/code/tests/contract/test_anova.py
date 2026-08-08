"""Contract tests for ANOVA output schema (US-2).

These tests verify that the ANOVA analysis module produces output conforming
to the expected schema defined in the project specification. They do NOT
re-implement the ANOVA logic; they validate the structure of the output
produced by the actual implementation.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest

# Import the ANOVA module symbols we are testing against
from analysis.anova import (
    ANOVAOutput,
    compute_two_way_anova,
    load_experiment_results,
    prepare_data_for_anova,
    run_anova_analysis,
)


class TestANOVAOutputSchema:
    """Test that ANOVAOutput dataclass conforms to the required schema."""

    def test_anova_output_has_required_fields(self):
        """ANOVAOutput must contain: interaction_p_value, main_effects, model_summary."""
        # Create a minimal valid instance
        output = ANOVAOutput(
            interaction_p_value=0.042,
            main_effects={
                "context_condition": {"f_stat": 5.2, "p_value": 0.023},
                "metric_name": {"f_stat": 8.1, "p_value": 0.005},
            },
            model_summary={"r_squared": 0.45, "n_observations": 400},
            bonferroni_corrected_alpha=0.025,
            raw_output={"test_statistic": 4.12, "degrees_of_freedom": (1, 396)},
        )

        # Verify all required attributes exist and have correct types
        assert hasattr(output, "interaction_p_value")
        assert isinstance(output.interaction_p_value, float)
        assert 0.0 <= output.interaction_p_value <= 1.0

        assert hasattr(output, "main_effects")
        assert isinstance(output.main_effects, dict)
        for factor, stats in output.main_effects.items():
            assert isinstance(stats, dict)
            assert "f_stat" in stats
            assert "p_value" in stats

        assert hasattr(output, "model_summary")
        assert isinstance(output.model_summary, dict)
        assert "r_squared" in output.model_summary
        assert "n_observations" in output.model_summary

    def test_anova_output_serialization(self):
        """ANOVAOutput must be JSON-serializable (for report generation)."""
        output = ANOVAOutput(
            interaction_p_value=0.031,
            main_effects={"context_condition": {"f_stat": 3.4, "p_value": 0.067}},
            model_summary={"r_squared": 0.12, "n_observations": 200},
            bonferroni_corrected_alpha=0.025,
            raw_output={"test_statistic": 2.91, "degrees_of_freedom": (1, 198)},
        )

        # Convert to dict and serialize
        data = {
            "interaction_p_value": output.interaction_p_value,
            "main_effects": output.main_effects,
            "model_summary": output.model_summary,
            "bonferroni_corrected_alpha": output.bonferroni_corrected_alpha,
            "raw_output": output.raw_output,
        }
        json_str = json.dumps(data)
        assert isinstance(json_str, str)

        # Deserialize and verify
        restored = json.loads(json_str)
        assert restored["interaction_p_value"] == 0.031
        assert "context_condition" in restored["main_effects"]

class TestANOVADataLoading:
    """Test that ANOVA data loading functions handle expected input formats."""

    def test_load_experiment_results_full_csv(self, tmp_path: Path):
        """load_experiment_results must read results_full.csv schema correctly."""
        csv_path = tmp_path / "results_full.csv"
        csv_path.write_text(
            "game_id,specialization_index,retrieval_efficiency,context_condition,agent_count\n"
            "1,0.35,0.72,full,5\n"
            "2,0.41,0.68,full,5\n"
            "3,0.29,0.81,full,5\n"
        )

        df = load_experiment_results(str(csv_path))
        assert df is not None
        assert "specialization_index" in df.columns
        assert "retrieval_efficiency" in df.columns
        assert "context_condition" in df.columns
        assert len(df) == 3

    def test_load_experiment_results_limited_csv(self, tmp_path: Path):
        """load_experiment_results must read results_limited.csv schema correctly."""
        csv_path = tmp_path / "results_limited.csv"
        csv_path.write_text(
            "game_id,specialization_index,retrieval_efficiency,context_condition,agent_count\n"
            "1,0.38,0.65,limited,5\n"
            "2,0.44,0.61,limited,5\n"
        )

        df = load_experiment_results(str(csv_path))
        assert df is not None
        assert len(df) == 2
        assert all(df["context_condition"] == "limited")

class TestANOVADataPreparation:
    """Test that prepare_data_for_anova produces correct long-format structure."""

    def test_prepare_data_creates_long_format(self, tmp_path: Path):
        """prepare_data_for_anova must transform wide to long format with metric_name column."""
        csv_path = tmp_path / "results_full.csv"
        csv_path.write_text(
            "game_id,specialization_index,retrieval_efficiency,context_condition,agent_count\n"
            "1,0.35,0.72,full,5\n"
            "2,0.41,0.68,full,5\n"
        )

        df = load_experiment_results(str(csv_path))
        long_df = prepare_data_for_anova(df)

        # Verify long-format structure
        assert "metric_name" in long_df.columns
        assert "metric_value" in long_df.columns
        assert "context_condition" in long_df.columns

        # Each original row should produce two rows (one per metric)
        assert len(long_df) == len(df) * 2

        # Verify metric names
        unique_metrics = set(long_df["metric_name"].unique())
        assert unique_metrics == {"specialization", "retrieval"}

class TestANOVAComputation:
    """Test that compute_two_way_anova returns valid statistical results."""

    def test_compute_two_way_anova_returns_p_values(self, tmp_path: Path):
        """compute_two_way_anova must return p-values for interaction and main effects."""
        # Create synthetic but realistic data (NOT fabricated results - just structure)
        csv_path = tmp_path / "results_combined.csv"
        csv_path.write_text(
            "game_id,specialization_index,retrieval_efficiency,context_condition,agent_count\n"
            "1,0.35,0.72,full,5\n"
            "2,0.41,0.68,full,5\n"
            "3,0.38,0.65,limited,5\n"
            "4,0.44,0.61,limited,5\n"
            "5,0.33,0.75,full,5\n"
            "6,0.39,0.69,full,5\n"
            "7,0.40,0.64,limited,5\n"
            "8,0.42,0.62,limited,5\n"
        )

        df = load_experiment_results(str(csv_path))
        long_df = prepare_data_for_anova(df)

        # Run ANOVA
        result = compute_two_way_anova(long_df)

        # Verify result structure
        assert result is not None
        assert isinstance(result, ANOVAOutput)

        # Verify p-value ranges
        assert 0.0 <= result.interaction_p_value <= 1.0
        for factor, stats in result.main_effects.items():
            assert 0.0 <= stats["p_value"] <= 1.0
            assert stats["f_stat"] >= 0.0

    def test_compute_two_way_anova_interaction_term(self, tmp_path: Path):
        """ANOVA must include interaction term C(context_condition):C(metric_name)."""
        csv_path = tmp_path / "results_combined.csv"
        csv_path.write_text(
            "game_id,specialization_index,retrieval_efficiency,context_condition,agent_count\n"
            "1,0.35,0.72,full,5\n"
            "2,0.41,0.68,full,5\n"
            "3,0.38,0.65,limited,5\n"
            "4,0.44,0.61,limited,5\n"
        )

        df = load_experiment_results(str(csv_path))
        long_df = prepare_data_for_anova(df)

        result = compute_two_way_anova(long_df)

        # The interaction p-value must be present (even if not significant)
        assert hasattr(result, "interaction_p_value")
        assert isinstance(result.interaction_p_value, float)

class TestANOVAAnalysisPipeline:
    """Test the full ANOVA analysis pipeline from file I/O to result."""

    def test_run_anova_analysis_end_to_end(self, tmp_path: Path):
        """run_anova_analysis must process full and limited results and return valid output."""
        # Create full context results
        full_csv = tmp_path / "results_full.csv"
        full_csv.write_text(
            "game_id,specialization_index,retrieval_efficiency,context_condition,agent_count\n"
            "1,0.35,0.72,full,5\n"
            "2,0.41,0.68,full,5\n"
            "3,0.29,0.81,full,5\n"
            "4,0.33,0.75,full,5\n"
            "5,0.38,0.69,full,5\n"
        )

        # Create limited context results
        limited_csv = tmp_path / "results_limited.csv"
        limited_csv.write_text(
            "game_id,specialization_index,retrieval_efficiency,context_condition,agent_count\n"
            "1,0.38,0.65,limited,5\n"
            "2,0.44,0.61,limited,5\n"
            "3,0.40,0.64,limited,5\n"
            "4,0.42,0.62,limited,5\n"
            "5,0.39,0.66,limited,5\n"
        )

        # Run analysis
        result = run_anova_analysis(
            full_results_path=str(full_csv),
            limited_results_path=str(limited_csv),
        )

        # Verify output schema
        assert result is not None
        assert isinstance(result, ANOVAOutput)
        assert 0.0 <= result.interaction_p_value <= 1.0
        assert "context_condition" in result.main_effects
        assert "metric_name" in result.main_effects
        assert "r_squared" in result.model_summary
        assert "n_observations" in result.model_summary

class TestANOVAErrorHandling:
    """Test that ANOVA functions fail gracefully on invalid input."""

    def test_load_experiment_results_missing_file(self):
        """load_experiment_results must raise FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            load_experiment_results("/nonexistent/path/results.csv")

    def test_prepare_data_for_anova_missing_columns(self, tmp_path: Path):
        """prepare_data_for_anova must handle missing required columns."""
        csv_path = tmp_path / "bad_results.csv"
        csv_path.write_text(
            "game_id,context_condition\n"  # Missing specialization_index, retrieval_efficiency
            "1,full\n"
        )

        df = load_experiment_results(str(csv_path))
        with pytest.raises((KeyError, ValueError)):
            prepare_data_for_anova(df)

    def test_compute_two_way_anova_insufficient_data(self, tmp_path: Path):
        """compute_two_way_anova must handle insufficient data for ANOVA."""
        csv_path = tmp_path / "tiny_results.csv"
        csv_path.write_text(
            "game_id,specialization_index,retrieval_efficiency,context_condition,agent_count\n"
            "1,0.35,0.72,full,5\n"  # Only one row - insufficient for ANOVA
        )

        df = load_experiment_results(str(csv_path))
        long_df = prepare_data_for_anova(df)

        # Should raise or return invalid result (implementation-dependent)
        # We test that it doesn't crash with an unexpected exception
        try:
            result = compute_two_way_anova(long_df)
            # If it returns a result, it should still have the schema
            assert isinstance(result, ANOVAOutput)
        except (ValueError, RuntimeError) as e:
            # Expected for insufficient data - as long as it's a clear error
            assert "insufficient" in str(e).lower() or "data" in str(e).lower()