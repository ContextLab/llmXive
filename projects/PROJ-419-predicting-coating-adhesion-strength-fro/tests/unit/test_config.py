"""
Unit tests for configuration loading.
"""
import pytest
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import config

class TestConfig:
    """Tests for configuration variables."""

    def test_max_rows_exists(self):
        """Test that MAX_ROWS is defined."""
        assert hasattr(config, 'MAX_ROWS')
        assert isinstance(config.MAX_ROWS, int)

    def test_ram_limit_exists(self):
        """Test that RAM_LIMIT_GB is defined."""
        assert hasattr(config, 'RAM_LIMIT_GB')
        assert isinstance(config.RAM_LIMIT_GB, (int, float))

    def test_timeout_hours_exists(self):
        """Test that TIMEOUT_HOURS is defined."""
        assert hasattr(config, 'TIMEOUT_HOURS')
        assert isinstance(config.TIMEOUT_HOURS, int)
