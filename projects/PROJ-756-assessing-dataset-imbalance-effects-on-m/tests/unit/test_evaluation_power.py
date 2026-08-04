import pytest
import numpy as np
import math
from pathlib import Path
import sys
import json

# Add parent directory to path to import code modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from evaluation import power_analysis_z_test, calculate_cohen_d, run_power_analysis

class TestPowerAnalysis:
    def test_cohen_d_identical_groups(self):
        """Cohen's d should be 0 for identical groups."""
        group1 = np.array([1, 2, 3, 4, 5])
        group2 = np.array([1, 2, 3, 4, 5])
        d = calculate_cohen_d(group1, group2)
        assert math.isclose(d, 0.0, abs_tol=1e-9)

    def test_cohen_d_positive_effect(self):
        """Cohen's d should be positive if group1 mean > group2 mean."""
        group1 = np.array([10, 12, 11, 13, 12])
        group2 = np.array([5, 6, 5, 7, 6])
        d = calculate_cohen_d(group1, group2)
        assert d > 0

    def test_power_analysis_sample_size(self):
        """Test that power analysis returns a reasonable sample size for d=0.5."""
        # Standard values: d=0.5, power=0.8, alpha=0.05
        # Expected n is approximately 64 per group (standard textbook value)
        n = power_analysis_z_test(effect_size=0.5, power=0.8, alpha=0.05)
        # Allow some tolerance due to approximation methods
        assert 60 <= n <= 70, f"Expected n around 64, got {n}"

    def test_power_analysis_effect_size_sensitivity(self):
        """Larger effect size should require smaller sample size."""
        n_small = power_analysis_z_test(effect_size=0.2, power=0.8, alpha=0.05)
        n_large = power_analysis_z_test(effect_size=0.8, power=0.8, alpha=0.05)
        assert n_small > n_large

    def test_run_power_analysis_output(self, tmp_path):
        """Test that run_power_analysis creates a valid JSON file."""
        output_file = tmp_path / "power_test.json"
        result = run_power_analysis(
            effect_size=0.5,
            power=0.8,
            alpha=0.05,
            output_path=output_file
        )
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            loaded = json.load(f)
        
        assert 'required_seeds_per_group' in loaded
        assert 'total_seeds' in loaded
        assert loaded['effect_size'] == 0.5
        assert loaded['power'] == 0.8
        assert loaded['alpha'] == 0.05
        assert loaded['required_seeds_per_group'] > 0
        assert loaded['total_seeds'] == loaded['required_seeds_per_group'] * 2