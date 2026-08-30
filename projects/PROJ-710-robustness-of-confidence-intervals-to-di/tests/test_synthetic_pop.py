"""
Tests for the synthetic population generator.
Verifies that the generated populations match the known ground truth parameters.
"""
import json
import os
import sys
import pytest
import numpy as np
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from code.data.synthetic_pop import (
    generate_synthetic_population,
    generate_regression_population_pair,
    calculate_lognormal_moments,
    N_SIM,
    POPULATION_SIZE,
    RANDOM_SEED
)
from code.config import Config


class TestSyntheticPopGenerator:
    """Test suite for synthetic population generation."""

    @pytest.fixture
    def config(self):
        return Config()

    @pytest.fixture
    def ground_truth_path(self, config):
        return config.data_dir / "ground_truth.json"

    def test_lognormal_moments(self):
        """Test calculation of log-normal mean and variance."""
        mu = 0.0
        sigma = 1.0
        # Mean = exp(0 + 0.5) = exp(0.5) ~ 1.6487
        # Var = (exp(1) - 1) * exp(1) ~ 1.718 * 2.718 ~ 4.67
        expected_mean = np.exp(0.5)
        expected_var = (np.exp(1) - 1) * np.exp(1)

        calc_mean, calc_var = calculate_lognormal_moments(mu, sigma)

        assert np.isclose(calc_mean, expected_mean, rtol=1e-5)
        assert np.isclose(calc_var, expected_var, rtol=1e-5)

    def test_ground_truth_file_exists(self, config):
        """Verify that the ground truth file is created."""
        # Run the generator first
        from code.data.synthetic_pop import main
        main()

        assert config.data_dir.exists()
        assert (config.data_dir / "ground_truth.json").exists()

    def test_ground_truth_parameters(self, config):
        """Verify the content of ground_truth.json."""
        from code.data.synthetic_pop import main
        main()

        gt_path = config.data_dir / "ground_truth.json"
        with open(gt_path, 'r') as f:
            data = json.load(f)

        assert "populations" in data
        assert len(data["populations"]) == 4

        # Check Adult Income
        adult = next(p for p in data["populations"] if p["id"] == "adult_income")
        assert adult["statistic_type"] == "mean"
        assert "ground_truth_mean" in adult
        assert adult["ground_truth_mean"] > 0

        # Check Regression
        reg = next(p for p in data["populations"] if p["id"] == "adult_regression")
        assert reg["statistic_type"] == "regression"
        assert reg["ground_truth_slope"] == 50.0
        assert reg["ground_truth_intercept"] == 1000.0

    def test_population_generation_reproducibility(self):
        """Test that generating populations with the same seed yields identical results."""
        pop1 = generate_synthetic_population("test", "normal", {"mean": 0, "std": 1}, n_pop=1, pop_size=100, seed=42)
        pop2 = generate_synthetic_population("test", "normal", {"mean": 0, "std": 1}, n_pop=1, pop_size=100, seed=42)

        assert np.array_equal(pop1[0], pop2[0])

    def test_regression_pair_generation(self):
        """Test that regression pairs are generated correctly."""
        pairs = generate_regression_population_pair(n_pop=1, pop_size=100, seed=42)
        assert len(pairs) == 1
        x, y = pairs[0]
        assert len(x) == 100
        assert len(y) == 100

        # Check linear relationship roughly (beta_1 = 50)
        # y = 1000 + 50*x + noise
        # Slope of y on x should be approx 50
        slope = np.polyfit(x, y, 1)[0]
        # Allow some tolerance due to noise
        assert 40 < slope < 60