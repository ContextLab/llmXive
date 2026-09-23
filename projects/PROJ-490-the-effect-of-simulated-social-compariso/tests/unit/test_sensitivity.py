"""
Unit test for parameter recovery bias calculation (|beta_hat - beta_true|).
This test verifies that the sensitivity analysis module correctly calculates
the bias between estimated coefficients and ground truth parameters when
synthetic data is used.

Note: This test relies on the ground truth parameters defined in the synthetic
data generator (T010) and the coefficient estimation from the regression model (T018).
"""

import pytest
import json
import os
import logging
from pathlib import Path
import sys
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis.sensitivity import (
    load_ground_truth_params,
    load_estimated_coefficients,
    calculate_parameter_recovery
)
from data.config import get_config

# Configure logging for the test
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestParameterRecoveryBias:
    """Tests for parameter recovery bias calculation."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.config = get_config()
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data"
        self.processed_dir = self.data_dir / "processed"
        self.state_dir = self.project_root / "state"

        # Ensure directories exist
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def test_load_ground_truth_params_from_seed_file(self):
        """Test loading ground truth parameters from synthetic seed file."""
        seed_file = self.data_dir / "raw" / "synthetic_seed.json"

        # Create a mock seed file if it doesn't exist for testing
        if not seed_file.exists():
            mock_params = {
                "ground_truth": {
                    "intercept": 0.0,
                    "main_effect_avatar": 0.1,
                    "main_effect_comparison": 0.1,
                    "interaction_beta": 0.2,
                    "noise_sigma": 1.0
                },
                "n_samples": 100,
                "seed": 42
            }
            seed_file.parent.mkdir(parents=True, exist_ok=True)
            with open(seed_file, 'w') as f:
                json.dump(mock_params, f, indent=2)

        params = load_ground_truth_params(str(seed_file))

        assert params is not None
        assert "intercept" in params
        assert "main_effect_avatar" in params
        assert "main_effect_comparison" in params
        assert "interaction_beta" in params
        assert "noise_sigma" in params

        # Verify expected values match T010 ground truth
        assert params["intercept"] == 0.0
        assert params["main_effect_avatar"] == 0.1
        assert params["main_effect_comparison"] == 0.1
        assert params["interaction_beta"] == 0.2

    def test_load_estimated_coefficients_from_csv(self):
        """Test loading estimated coefficients from regression output."""
        coeffs_file = self.processed_dir / "regression_coefficients.csv"

        # Create a mock coefficient file if it doesn't exist
        if not coeffs_file.exists():
            mock_coeffs = [
                {"name": "Intercept", "estimate": 0.05, "std_err": 0.1, "p_value": 0.6},
                {"name": "avatar_condition", "estimate": 0.12, "std_err": 0.15, "p_value": 0.42},
                {"name": "comparison_tendency", "estimate": 0.08, "std_err": 0.12, "p_value": 0.5},
                {"name": "avatar_condition:comparison_tendency", "estimate": 0.18, "std_err": 0.2, "p_value": 0.36}
            ]
            import pandas as pd
            df = pd.DataFrame(mock_coeffs)
            coeffs_file.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(coeffs_file, index=False)

        coeffs = load_estimated_coefficients(str(coeffs_file))

        assert coeffs is not None
        assert len(coeffs) > 0
        assert any(c["name"] == "Intercept" for c in coeffs)
        assert any(c["name"] == "avatar_condition" for c in coeffs)

    def test_calculate_parameter_recovery_bias(self):
        """Test the core bias calculation: |beta_hat - beta_true|."""
        # Define ground truth
        ground_truth = {
            "intercept": 0.0,
            "main_effect_avatar": 0.1,
            "main_effect_comparison": 0.1,
            "interaction_beta": 0.2
        }

        # Define estimated coefficients (with some noise)
        estimated = [
            {"name": "Intercept", "estimate": 0.05},
            {"name": "avatar_condition", "estimate": 0.12},
            {"name": "comparison_tendency", "estimate": 0.08},
            {"name": "avatar_condition:comparison_tendency", "estimate": 0.18}
        ]

        # Map estimated names to ground truth keys
        name_mapping = {
            "Intercept": "intercept",
            "avatar_condition": "main_effect_avatar",
            "comparison_tendency": "main_effect_comparison",
            "avatar_condition:comparison_tendency": "interaction_beta"
        }

        result = calculate_parameter_recovery(estimated, ground_truth, name_mapping)

        assert result is not None
        assert "bias" in result
        assert "absolute_errors" in result

        # Verify bias calculation for Intercept: |0.05 - 0.0| = 0.05
        assert result["absolute_errors"]["intercept"] == pytest.approx(0.05, abs=1e-6)
        # Verify bias calculation for avatar_condition: |0.12 - 0.1| = 0.02
        assert result["absolute_errors"]["main_effect_avatar"] == pytest.approx(0.02, abs=1e-6)
        # Verify bias calculation for interaction: |0.18 - 0.2| = 0.02
        assert result["absolute_errors"]["interaction_beta"] == pytest.approx(0.02, abs=1e-6)

        # The overall bias is the mean of absolute errors
        expected_mean_bias = (0.05 + 0.02 + 0.02 + 0.02) / 4
        assert result["bias"] == pytest.approx(expected_mean_bias, abs=1e-6)

    def test_parameter_recovery_with_perfect_estimates(self):
        """Test bias calculation when estimates perfectly match ground truth."""
        ground_truth = {
            "intercept": 0.0,
            "main_effect_avatar": 0.1,
            "main_effect_comparison": 0.1,
            "interaction_beta": 0.2
        }

        estimated = [
            {"name": "Intercept", "estimate": 0.0},
            {"name": "avatar_condition", "estimate": 0.1},
            {"name": "comparison_tendency", "estimate": 0.1},
            {"name": "avatar_condition:comparison_tendency", "estimate": 0.2}
        ]

        name_mapping = {
            "Intercept": "intercept",
            "avatar_condition": "main_effect_avatar",
            "comparison_tendency": "main_effect_comparison",
            "avatar_condition:comparison_tendency": "interaction_beta"
        }

        result = calculate_parameter_recovery(estimated, ground_truth, name_mapping)

        assert result["bias"] == pytest.approx(0.0, abs=1e-6)
        assert all(v == 0.0 for v in result["absolute_errors"].values())

    def test_parameter_recovery_handles_missing_coefficients(self):
        """Test that missing coefficients are handled gracefully."""
        ground_truth = {
            "intercept": 0.0,
            "main_effect_avatar": 0.1,
            "main_effect_comparison": 0.1,
            "interaction_beta": 0.2
        }

        # Missing "comparison_tendency" estimate
        estimated = [
            {"name": "Intercept", "estimate": 0.05},
            {"name": "avatar_condition", "estimate": 0.12},
            # Missing comparison_tendency
            {"name": "avatar_condition:comparison_tendency", "estimate": 0.18}
        ]

        name_mapping = {
            "Intercept": "intercept",
            "avatar_condition": "main_effect_avatar",
            "comparison_tendency": "main_effect_comparison",
            "avatar_condition:comparison_tendency": "interaction_beta"
        }

        result = calculate_parameter_recovery(estimated, ground_truth, name_mapping)

        assert result is not None
        # Should calculate bias only for available coefficients
        assert "main_effect_comparison" not in result["absolute_errors"]
        assert len(result["absolute_errors"]) == 3

    def test_integration_with_full_pipeline_artifacts(self):
        """
        Integration test: Calculate parameter recovery using actual artifacts
        generated by the pipeline (if they exist).
        """
        seed_file = self.data_dir / "raw" / "synthetic_seed.json"
        coeffs_file = self.processed_dir / "regression_coefficients.csv"

        # Only run if both files exist
        if not seed_file.exists() or not coeffs_file.exists():
            pytest.skip("Required artifacts (synthetic_seed.json, regression_coefficients.csv) not found. "
                        "Run the full pipeline first to generate these files.")

        # Load ground truth
        ground_truth = load_ground_truth_params(str(seed_file))

        # Load estimated coefficients
        estimated = load_estimated_coefficients(str(coeffs_file))

        # Map names
        name_mapping = {
            "Intercept": "intercept",
            "avatar_condition": "main_effect_avatar",
            "comparison_tendency": "main_effect_comparison",
            "avatar_condition:comparison_tendency": "interaction_beta"
        }

        # Calculate recovery
        result = calculate_parameter_recovery(estimated, ground_truth, name_mapping)

        assert result is not None
        assert result["bias"] >= 0.0
        assert "absolute_errors" in result
        assert len(result["absolute_errors"]) > 0

        logger.info(f"Parameter recovery bias: {result['bias']:.4f}")
        logger.info(f"Absolute errors: {result['absolute_errors']}")

    def test_bias_threshold_validation(self):
        """
        Test that the bias calculation correctly identifies when bias exceeds
        a specified threshold (used in sensitivity analysis).
        """
        ground_truth = {"interaction_beta": 0.2}
        estimated = [{"name": "avatar_condition:comparison_tendency", "estimate": 0.5}]
        name_mapping = {"avatar_condition:comparison_tendency": "interaction_beta"}

        result = calculate_parameter_recovery(estimated, ground_truth, name_mapping)

        # Bias should be |0.5 - 0.2| = 0.3
        assert result["absolute_errors"]["interaction_beta"] == pytest.approx(0.3, abs=1e-6)

        # Simulate a threshold check (e.g., threshold = 0.1)
        threshold = 0.1
        exceeds_threshold = result["absolute_errors"]["interaction_beta"] > threshold
        assert exceeds_threshold is True