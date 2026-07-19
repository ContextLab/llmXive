import pytest
import sys
from pathlib import Path
from simulation.config import CONFIG_MATRIX

class TestConfigMatrix:
    def test_config_matrix_exists(self):
        """T065: Verify CONFIG_MATRIX constant exists."""
        assert CONFIG_MATRIX is not None
        assert isinstance(CONFIG_MATRIX, list)

    def test_config_matrix_structure(self):
        """T065: Verify CONFIG_MATRIX structure."""
        assert len(CONFIG_MATRIX) > 0
        for block in CONFIG_MATRIX:
            assert "distribution_types" in block
            assert "scaling_methods" in block
            assert "test_types" in block
            assert isinstance(block["distribution_types"], list)
            assert isinstance(block["scaling_methods"], list)
            assert isinstance(block["test_types"], list)

    def test_required_distribution_types(self):
        """T065: Verify required distribution types are present."""
        all_dists = []
        for block in CONFIG_MATRIX:
            all_dists.extend(block["distribution_types"])
        assert "Normal" in all_dists
        assert "Skewed" in all_dists
        assert "Heteroscedastic" in all_dists

    def test_required_scaling_methods(self):
        """T065: Verify required scaling methods are present."""
        all_scales = []
        for block in CONFIG_MATRIX:
            all_scales.extend(block["scaling_methods"])
        assert "standardization" in all_scales
        assert "minmax" in all_scales
        assert "robust" in all_scales

    def test_required_test_types(self):
        """T065: Verify required test types are present."""
        all_tests = []
        for block in CONFIG_MATRIX:
            all_tests.extend(block["test_types"])
        assert "t-test" in all_tests
        assert "anova" in all_tests
        assert "chi-squared" in all_tests
