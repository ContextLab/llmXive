"""
Unit tests for the config module.
"""

import sys
import os
import tempfile
import pytest

# Add the code directory to the path so we can import utils.config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from utils.config import get_seed, check_memory_limit, set_memory_limit, get_memory_limit


class TestConfig:
    """Tests for the configuration module."""

    def test_get_seed_returns_int(self):
        """Test that get_seed returns an integer."""
        seed = get_seed()
        assert isinstance(seed, int)

    def test_get_seed_returns_expected_value(self):
        """Test that get_seed returns the expected default value (42)."""
        seed = get_seed()
        assert seed == 42

    def test_check_memory_limit_returns_bool(self):
        """Test that check_memory_limit returns a boolean."""
        result = check_memory_limit()
        assert isinstance(result, bool)

    def test_check_memory_limit_within_limit(self):
        """Test that check_memory_limit returns True when within limit."""
        # Set a very high limit to ensure we're within it
        original_limit = get_memory_limit()
        try:
            set_memory_limit(10 * 1024**3)  # 10GB
            assert check_memory_limit() is True
        finally:
            set_memory_limit(original_limit)

    def test_set_and_get_memory_limit(self):
        """Test that set_memory_limit and get_memory_limit work correctly."""
        original_limit = get_memory_limit()
        new_limit = 5 * 1024**3  # 5GB
        try:
            set_memory_limit(new_limit)
            assert get_memory_limit() == new_limit
        finally:
            set_memory_limit(original_limit)

    def test_memory_limit_env_variable(self):
        """Test that MEMORY_LIMIT_BYTES environment variable is respected."""
        original_limit = get_memory_limit()
        try:
            # Set a custom limit via environment variable
            os.environ["MEMORY_LIMIT_BYTES"] = "1073741824"  # 1GB
            # Re-import to pick up the new value (this is a bit hacky but works for testing)
            import importlib
            import utils.config
            importlib.reload(utils.config)
            from utils.config import get_memory_limit as new_get_memory_limit
            assert new_get_memory_limit() == 1073741824
        finally:
            # Restore original state
            if "MEMORY_LIMIT_BYTES" in os.environ:
                del os.environ["MEMORY_LIMIT_BYTES"]
            importlib.reload(utils.config)