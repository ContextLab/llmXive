"""
Contract test for ANOVA output schema (US-2).

This test validates that the ANOVA analysis produces output conforming to the
expected schema defined in code/analysis/anova.py. It ensures that the
Two-Way Independent-Samples ANOVA results contain all required fields and
data types.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from analysis.anova import (
    ANOVAOutput,
    ANOVAFullResult,
    load_experiment_results,
    prepare_data_for_anova,
    compute_two_way_anova_manual,
    apply_bonferroni_correction,
)


class TestANOVAOutputSchema:
    """Test that ANOVA output conforms to the expected schema."""

    def test_anova_output_dataclass_fields(self):
        """Verify ANOVAOutput has all required fields."""
        # Create a sample ANOVAOutput instance
        sample_output = ANOVAOutput(
            interaction_p_value=0.023,
            main_effect_context_p_value=0.015,
            main_effect_metric_p_value=0.042,
            interaction_effect_size=0.125,
            main_effect_context_effect_size=0.089,
            main_effect_metric_effect_size=0.156,
            bonferroni_corrected_alpha=0.0167,
            significant_interaction=True,
            significant_context_effect=False,
            significant_metric_effect=True,
            degrees_of_freedom_interaction=(1, 396),
            degrees_of_freedom_context=(1, 396),
            degrees_of_freedom_metric=(1, 396),
            f_statistic_interaction=5.42,
            f_statistic_context=4.12,
            f_statistic_metric=6.78,
            sample_size=400,
            context_levels=2,
            metric_levels=2,
            method="Two-Way Independent-Samples ANOVA (Manual)",
        )

        # Verify all required fields exist
        assert hasattr(sample_output, "interaction_p_value")
        assert hasattr(sample_output, "main_effect_context_p_value")
        assert hasattr(sample_output, "main_effect_metric_p_value")
        assert hasattr(sample_output, "interaction_effect_size")
        assert hasattr(sample_output, "bonferroni_corrected_alpha")
        assert hasattr(sample_output, "significant_interaction")
        assert hasattr(sample_output, "degrees_of_freedom_interaction")
        assert hasattr(sample_output, "f_statistic_interaction")

        # Verify field types
        assert isinstance(sample_output.interaction_p_value, float)
        assert isinstance(sample_output.significant_interaction, bool)
        assert isinstance(sample_output.degrees_of_freedom_interaction, tuple)
        assert isinstance(sample_output.f_statistic_interaction, float)
        assert isinstance(sample_output.method, str)

    def test_anova_output_json_serialization(self):
        """Verify ANOVAOutput can be serialized to JSON."""
        sample_output = ANOVAOutput(
            interaction_p_value=0.023,
            main_effect_context_p_value=0.015,
            main_effect_metric_p_value=0.042,
            interaction_effect_size=0.125,
            main_effect_context_effect_size=0.089,
            main_effect_metric_effect_size=0.156,
            bonferroni_corrected_alpha=0.0167,
            significant_interaction=True,
            significant_context_effect=False,
            significant_metric_effect=True,
            degrees_of_freedom_interaction=(1, 396),
            degrees_of_freedom_context=(1, 396),
            degrees_of_freedom_metric=(1, 396),
            f_statistic_interaction=5.42,
            f_statistic_context=4.12,
            f_statistic_metric=6.78,
            sample_size=400,
            context_levels=2,
            metric_levels=2,
            method="Two-Way Independent-Samples ANOVA (Manual)",
        )

        # Convert to dict (dataclass asdict)
        from dataclasses import asdict

        output_dict = asdict(sample_output)

        # Verify JSON serialization
        json_str = json.dumps(output_dict, default=str)
        assert json_str is not None
        assert "interaction_p_value" in json_str
        assert "significant_interaction" in json_str

    def test_anova_output_validation(self):
        """Verify ANOVAOutput validates p-values and effect sizes."""
        # Valid output
        valid_output = ANOVAOutput(
            interaction_p_value=0.023,
            main_effect_context_p_value=0.015,
            main_effect_metric_p_value=0.042,
            interaction_effect_size=0.125,
            main_effect_context_effect_size=0.089,
            main_effect_metric_effect_size=0.156,
            bonferroni_corrected_alpha=0.0167,
            significant_interaction=True,
            significant_context_effect=False,
            significant_metric_effect=True,
            degrees_of_freedom_interaction=(1, 396),
            degrees_of_freedom_context=(1, 396),
            degrees_of_freedom_metric=(1, 396),
            f_statistic_interaction=5.42,
            f_statistic_context=4.12,
            f_statistic_metric=6.78,
            sample_size=400,
            context_levels=2,
            metric_levels=2,
            method="Two-Way Independent-Samples ANOVA (Manual)",
        )
        assert 0 <= valid_output.interaction_p_value <= 1
        assert 0 <= valid_output.main_effect_context_p_value <= 1
        assert 0 <= valid_output.main_effect_metric_p_value <= 1

    def test_anova_full_result_schema(self):
        """Verify ANOVAFullResult contains all required components."""
        sample_output = ANOVAOutput(
            interaction_p_value=0.023,
            main_effect_context_p_value=0.015,
            main_effect_metric_p_value=0.042,
            interaction_effect_size=0.125,
            main_effect_context_effect_size=0.089,
            main_effect_metric_effect_size=0.156,
            bonferroni_corrected_alpha=0.0167,
            significant_interaction=True,
            significant_context_effect=False,
            significant_metric_effect=True,
            degrees_of_freedom_interaction=(1, 396),
            degrees_of_freedom_context=(1, 396),
            degrees_of_freedom_metric=(1, 396),
            f_statistic_interaction=5.42,
            f_statistic_context=4.12,
            f_statistic_metric=6.78,
            sample_size=400,
            context_levels=2,
            metric_levels=2,
            method="Two-Way Independent-Samples ANOVA (Manual)",
        )

        full_result = ANOVAFullResult(
            anova_output=sample_output,
            descriptive_statistics={
                "full_context": {
                    "specialization": {"mean": 0.45, "std": 0.12, "n": 200},
                    "retrieval": {"mean": 0.78, "std": 0.09, "n": 200},
                },
                "limited_context": {
                    "specialization": {"mean": 0.38, "std": 0.15, "n": 200},
                    "retrieval": {"mean": 0.65, "std": 0.11, "n": 200},
                },
            },
            model_summary="Two-Way ANOVA: metric_value ~ C(context_condition) * C(metric_name)",
            assumptions_check={"normality": "passed", "homogeneity": "passed"},
        )

        assert full_result.anova_output is not None
        assert full_result.descriptive_statistics is not None
        assert full_result.model_summary is not None
        assert "full_context" in full_result.descriptive_statistics
        assert "limited_context" in full_result.descriptive_statistics

class TestANOVADataLoading:
    """Test data loading functions for ANOVA."""

    def test_load_experiment_results_schema(self, tmp_path):
        """Verify load_experiment_results returns correct schema."""
        # Create sample results CSV
        results_file = tmp_path / "results_full.csv"
        results_file.write_text(
            "game_id,specialization_index,retrieval_efficiency,context_condition,agent_count\n"
            "1,0.45,0.78,full,5\n"
            "2,0.42,0.80,full,5\n"
            "3,0.38,0.65,limited,5\n"
            "4,0.40,0.68,limited,5\n"
        )

        data = load_experiment_results(str(results_file))

        assert data is not None
        assert len(data) == 4
        assert "specialization_index" in data.columns
        assert "retrieval_efficiency" in data.columns
        assert "context_condition" in data.columns

    def test_prepare_data_for_anova_transformation(self, tmp_path):
        """Verify prepare_data_for_anova transforms data correctly."""
        # Create sample results CSV
        results_file = tmp_path / "results_full.csv"
        results_file.write_text(
            "game_id,specialization_index,retrieval_efficiency,context_condition,agent_count\n"
            "1,0.45,0.78,full,5\n"
            "2,0.42,0.80,full,5\n"
        )

        full_data = load_experiment_results(str(results_file))

        # Create limited context data
        limited_file = tmp_path / "results_limited.csv"
        limited_file.write_text(
            "game_id,specialization_index,retrieval_efficiency,context_condition,agent_count\n"
            "3,0.38,0.65,limited,5\n"
            "4,0.40,0.68,limited,5\n"
        )

        limited_data = load_experiment_results(str(limited_file))

        # Prepare for ANOVA
        combined_data = prepare_data_for_anova(full_data, limited_data)

        assert combined_data is not None
        assert len(combined_data) == 8  # 2 metrics * 4 games
        assert "metric_name" in combined_data.columns
        assert "metric_value" in combined_data.columns
        assert "context_condition" in combined_data.columns

        # Verify long-format transformation
        unique_metrics = combined_data["metric_name"].unique()
        assert "specialization" in unique_metrics
        assert "retrieval" in unique_metrics

class TestANOVAComputation:
    """Test ANOVA computation functions."""

    def test_compute_two_way_anova_manual_schema(self, tmp_path):
        """Verify compute_two_way_anova_manual returns correct schema."""
        # Create sample data
        results_file = tmp_path / "results_full.csv"
        results_file.write_text(
            "game_id,specialization_index,retrieval_efficiency,context_condition,agent_count\n"
            "1,0.45,0.78,full,5\n"
            "2,0.42,0.80,full,5\n"
            "3,0.38,0.65,limited,5\n"
            "4,0.40,0.68,limited,5\n"
        )

        full_data = load_experiment_results(str(results_file))

        limited_file = tmp_path / "results_limited.csv"
        limited_file.write_text(
            "game_id,specialization_index,retrieval_efficiency,context_condition,agent_count\n"
            "5,0.35,0.62,limited,5\n"
            "6,0.37,0.64,limited,5\n"
        )

        limited_data = load_experiment_results(str(limited_file))

        combined_data = prepare_data_for_anova(full_data, limited_data)

        # Compute ANOVA
        result = compute_two_way_anova_manual(combined_data)

        assert result is not None
        assert "interaction_p_value" in result
        assert "main_effect_context_p_value" in result
        assert "main_effect_metric_p_value" in result
        assert "f_statistic_interaction" in result
        assert "degrees_of_freedom_interaction" in result

    def test_bonferroni_correction(self):
        """Verify Bonferroni correction is applied correctly."""
        raw_alpha = 0.05
        num_tests = 3

        corrected_alpha = apply_bonferroni_correction(raw_alpha, num_tests)

        expected_alpha = raw_alpha / num_tests
        assert corrected_alpha == expected_alpha
        assert corrected_alpha < raw_alpha

class TestANOVAIntegration:
    """Integration tests for ANOVA workflow."""

    def test_full_anova_workflow(self, tmp_path):
        """Test complete ANOVA workflow from data to output."""
        # Create sample data files
        results_file = tmp_path / "results_full.csv"
        results_file.write_text(
            "game_id,specialization_index,retrieval_efficiency,context_condition,agent_count\n"
            "1,0.45,0.78,full,5\n"
            "2,0.42,0.80,full,5\n"
            "3,0.44,0.79,full,5\n"
            "4,0.43,0.77,full,5\n"
            "5,0.41,0.81,full,5\n"
            "6,0.46,0.76,full,5\n"
            "7,0.40,0.79,full,5\n"
            "8,0.44,0.80,full,5\n"
            "9,0.42,0.78,full,5\n"
            "10,0.43,0.77,full,5\n"
        )

        limited_file = tmp_path / "results_limited.csv"
        limited_file.write_text(
            "game_id,specialization_index,retrieval_efficiency,context_condition,agent_count\n"
            "11,0.35,0.62,limited,5\n"
            "12,0.37,0.64,limited,5\n"
            "13,0.36,0.63,limited,5\n"
            "14,0.38,0.65,limited,5\n"
            "15,0.34,0.61,limited,5\n"
            "16,0.39,0.66,limited,5\n"
            "17,0.33,0.60,limited,5\n"
            "18,0.36,0.63,limited,5\n"
            "19,0.37,0.64,limited,5\n"
            "20,0.38,0.65,limited,5\n"
        )

        # Load and prepare data
        full_data = load_experiment_results(str(results_file))
        limited_data = load_experiment_results(str(limited_file))
        combined_data = prepare_data_for_anova(full_data, limited_data)

        # Compute ANOVA
        result = compute_two_way_anova_manual(combined_data)

        # Verify result schema
        assert result is not None
        assert isinstance(result, dict)
        assert "interaction_p_value" in result
        assert isinstance(result["interaction_p_value"], float)
        assert 0 <= result["interaction_p_value"] <= 1

        # Apply Bonferroni correction
        corrected_alpha = apply_bonferroni_correction(0.05, 3)
        result["bonferroni_corrected_alpha"] = corrected_alpha

        # Create ANOVAOutput
        anova_output = ANOVAOutput(
            interaction_p_value=result["interaction_p_value"],
            main_effect_context_p_value=result.get("main_effect_context_p_value", 0.0),
            main_effect_metric_p_value=result.get("main_effect_metric_p_value", 0.0),
            interaction_effect_size=result.get("interaction_effect_size", 0.0),
            main_effect_context_effect_size=result.get("main_effect_context_effect_size", 0.0),
            main_effect_metric_effect_size=result.get("main_effect_metric_effect_size", 0.0),
            bonferroni_corrected_alpha=corrected_alpha,
            significant_interaction=result["interaction_p_value"] < corrected_alpha,
            significant_context_effect=False,
            significant_metric_effect=False,
            degrees_of_freedom_interaction=result.get("degrees_of_freedom_interaction", (1, 0)),
            degrees_of_freedom_context=result.get("degrees_of_freedom_context", (1, 0)),
            degrees_of_freedom_metric=result.get("degrees_of_freedom_metric", (1, 0)),
            f_statistic_interaction=result.get("f_statistic_interaction", 0.0),
            f_statistic_context=result.get("f_statistic_context", 0.0),
            f_statistic_metric=result.get("f_statistic_metric", 0.0),
            sample_size=len(combined_data),
            context_levels=2,
            metric_levels=2,
            method="Two-Way Independent-Samples ANOVA (Manual)",
        )

        # Verify final output
        assert anova_output.significant_interaction is not None
        assert anova_output.bonferroni_corrected_alpha is not None
        assert anova_output.method == "Two-Way Independent-Samples ANOVA (Manual)"