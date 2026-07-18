"""
Unit tests for data validation contracts (T005).
Ensures schemas are valid JSON and correctly validate sample data.
"""
import json
import pytest
from pathlib import Path

from code.config import get_project_root
from code.utils.validator import (
    load_schema,
    validate_trajectory_data,
    validate_metrics_data,
    validate_file_against_schema
)


class TestSchemaLoading:
    def test_load_trajectory_schema_exists(self):
        schema = load_schema("trajectory_schema.json")
        assert "$schema" in schema
        assert schema["title"] == "CHERRL Trajectory Divergence Schema"

    def test_load_metrics_schema_exists(self):
        schema = load_schema("metrics_schema.json")
        assert "$schema" in schema
        assert schema["title"] == "Evaluation Metrics Schema"


class TestTrajectoryValidation:
    def test_valid_trajectory_data(self):
        valid_data = {
            "metadata": {
                "source_dataset": "cherrl",
                "processing_version": "1.0.0",
                "seed_ids": ["seed_001"]
            },
            "data": [
                {
                    "step": 0,
                    "seed_id": "seed_001",
                    "bias_type": "Lexical",
                    "J_biased": 0.85,
                    "J_unbiased": 0.80,
                    "G_t": 0.05,
                    "dG_t": 0.00,
                    "z_score_G": 0.00,
                    "hacked_label": False
                }
            ]
        }
        # Should not raise
        assert validate_trajectory_data(valid_data) is True

    def test_invalid_trajectory_missing_required_field(self):
        invalid_data = {
            "metadata": {
                "source_dataset": "cherrl",
                "processing_version": "1.0.0",
                "seed_ids": []
            },
            "data": [
                {
                    "step": 0,
                    "seed_id": "seed_001",
                    "bias_type": "Lexical",
                    "J_biased": 0.85,
                    "J_unbiased": 0.80
                    # Missing G_t, dG_t, etc.
                }
            ]
        }
        with pytest.raises(Exception):  # jsonschema.exceptions.ValidationError
            validate_trajectory_data(invalid_data)

    def test_invalid_bias_type(self):
        invalid_data = {
            "metadata": {
                "source_dataset": "cherrl",
                "processing_version": "1.0.0",
                "seed_ids": []
            },
            "data": [
                {
                    "step": 0,
                    "seed_id": "seed_001",
                    "bias_type": "InvalidType",  # Not in enum
                    "J_biased": 0.85,
                    "J_unbiased": 0.80,
                    "G_t": 0.05,
                    "dG_t": 0.00,
                    "z_score_G": 0.00,
                    "hacked_label": False
                }
            ]
        }
        with pytest.raises(Exception):
            validate_trajectory_data(invalid_data)


class TestMetricsValidation:
    def test_valid_metrics_data(self):
        valid_data = {
            "metadata": {
                "evaluation_version": "1.0.0",
                "threshold_config": {
                    "z_score_threshold": 3.0,
                    "dG_threshold_multiplier": 1.5
                }
            },
            "global_metrics": {
                "precision": 0.85,
                "recall": 0.80,
                "f1_score": 0.82,
                "accuracy": 0.90
            },
            "metrics_by_bias_type": {
                "Lexical": {
                    "precision": 0.85,
                    "recall": 0.80,
                    "f1_score": 0.82,
                    "sample_count": 100
                }
            },
            "statistical_tests": {
                "wilcoxon_test": {
                    "statistic": 10.5,
                    "p_value": 0.03,
                    "effect_size": 0.5,
                    "baseline_name": "random-guess"
                },
                "independence_check": {
                    "j_unbiased_vs_gold_corr": 0.3,
                    "j_biased_vs_gold_corr": 0.2,
                    "threshold": 0.8,
                    "passed": True
                }
            },
            "ground_truth_stats": {
                "total_hacked_steps": 50,
                "total_steps": 1000,
                "hacking_rate": 0.05
            }
        }
        assert validate_metrics_data(valid_data) is True

    def test_invalid_metrics_missing_required(self):
        invalid_data = {
            "metadata": {
                "evaluation_version": "1.0.0",
                "threshold_config": {}
            },
            "global_metrics": {},
            "metrics_by_bias_type": {},
            "statistical_tests": {},
            "ground_truth_stats": {}
        }
        with pytest.raises(Exception):
            validate_metrics_data(invalid_data)
