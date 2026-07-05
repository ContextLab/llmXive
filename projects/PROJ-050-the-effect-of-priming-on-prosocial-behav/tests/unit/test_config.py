"""Unit tests for configuration management."""
import os
from pathlib import Path

import pytest

from code.config import PROJECT_ROOT, TARGET_N, ALPHA, EFFECT_SIZE_D, MIN_GROUP_SIZE


class TestConfig:
    """Test suite for code/config.py."""

    def test_project_root_exists(self):
        """Test that PROJECT_ROOT is a valid Path."""
        assert isinstance(PROJECT_ROOT, Path)
        assert PROJECT_ROOT.exists()

    def test_target_n_is_integer(self):
        """Test that TARGET_N is an integer."""
        assert isinstance(TARGET_N, int)
        assert TARGET_N > 0

    def test_alpha_is_float(self):
        """Test that ALPHA is a float between 0 and 1."""
        assert isinstance(ALPHA, float)
        assert 0 < ALPHA < 1

    def test_effect_size_d_is_float(self):
        """Test that EFFECT_SIZE_D is a positive float."""
        assert isinstance(EFFECT_SIZE_D, float)
        assert EFFECT_SIZE_D > 0

    def test_min_group_size_is_integer(self):
        """Test that MIN_GROUP_SIZE is an integer."""
        assert isinstance(MIN_GROUP_SIZE, int)
        assert MIN_GROUP_SIZE > 0
