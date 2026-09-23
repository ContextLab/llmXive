"""
Unit tests for statistical power analysis and sample size calculation.
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analysis.statistical_tests import (
    calculate_power_and_sample_size,
    check_power_requirement,
    generate_batch_config
)


class TestStatisticalPower:
    """Tests for statistical power functions."""

    def test_calculate_sample_size_medium_effect(self):
        """Test sample size calculation with medium effect size (0.25)."""
        n = calculate_power_and_sample_size(
            alpha=0.05,
            power=0.8,
            effect_size=0.25
        )
        # For medium effect size with 3 groups, we expect N around 50-60 per group
        assert n > 0
        assert isinstance(n, int)
        # Verify the calculated N actually achieves the desired power
        meets, achieved_power = check_power_requirement(n, 0.05, 0.8, 0.25)
        assert meets, f"Calculated N={n} does not achieve power >= 0.8 (achieved: {achieved_power})"

    def test_calculate_sample_size_large_effect(self):
        """Test sample size calculation with large effect size (0.4)."""
        n = calculate_power_and_sample_size(
            alpha=0.05,
            power=0.8,
            effect_size=0.4
        )
        # Larger effect size should require smaller sample size
        assert n > 0
        assert isinstance(n, int)
        meets, _ = check_power_requirement(n, 0.05, 0.8, 0.4)
        assert meets

    def test_calculate_sample_size_small_effect(self):
        """Test sample size calculation with small effect size (0.1)."""
        n = calculate_power_and_sample_size(
            alpha=0.05,
            power=0.8,
            effect_size=0.1
        )
        # Smaller effect size should require larger sample size
        assert n > 0
        assert isinstance(n, int)
        # Should be larger than for medium effect
        n_medium = calculate_power_and_sample_size(effect_size=0.25)
        assert n > n_medium

    def test_check_power_requirement(self):
        """Test power requirement checking."""
        # A very large sample should definitely meet the requirement
        meets, power = check_power_requirement(
            current_n=1000,
            alpha=0.05,
            power=0.8,
            effect_size=0.25
        )
        assert meets
        assert power >= 0.8

        # A very small sample might not meet the requirement
        meets, power = check_power_requirement(
            current_n=5,
            alpha=0.05,
            power=0.8,
            effect_size=0.25
        )
        # This might or might not meet, but we can check the logic
        assert isinstance(meets, bool)
        assert 0 <= power <= 1

    def test_generate_batch_config(self):
        """Test batch config generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'batch_config.json')
            conditions = ['sequential', 'mixed', 'coevolving']
            n_per_condition = 30

            config = generate_batch_config(
                output_path=output_path,
                n_per_condition=n_per_condition,
                conditions=conditions
            )

            # Verify file was created
            assert os.path.exists(output_path)

            # Verify config structure
            assert config['n_per_condition'] == n_per_condition
            assert config['conditions'] == conditions
            assert 'seeds' in config

            # Verify seeds for each condition
            for cond in conditions:
                assert cond in config['seeds']
                assert len(config['seeds'][cond]) == n_per_condition
                # Verify seeds are unique within a condition
                assert len(set(config['seeds'][cond])) == n_per_condition
                # Verify seeds are integers
                for seed in config['seeds'][cond]:
                    assert isinstance(seed, int)

    def test_generate_batch_config_default_conditions(self):
        """Test batch config generation with default conditions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'batch_config.json')

            config = generate_batch_config(
                output_path=output_path,
                n_per_condition=30
            )

            expected_conditions = ['sequential', 'mixed', 'coevolving']
            assert config['conditions'] == expected_conditions

    def test_generate_batch_config_file_content(self):
        """Test that the generated file is valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'batch_config.json')

            generate_batch_config(output_path=output_path, n_per_condition=30)

            with open(output_path, 'r') as f:
                loaded_config = json.load(f)

            assert 'seeds' in loaded_config
            assert 'sequential' in loaded_config['seeds']
            assert len(loaded_config['seeds']['sequential']) == 30
