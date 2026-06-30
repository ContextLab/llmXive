import pytest
import sys
import time
from pathlib import Path

# Add src to path if needed, though pytest usually handles this with conftest
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.lib.memory_monitor import (
    get_current_memory_usage_bytes,
    check_memory_limit,
    format_bytes,
    MEMORY_LIMIT_GB,
    memory_monitor_context
)
from src.lib.config import get_logger

class TestMemoryMonitor:
    def test_get_current_memory_usage_bytes_returns_positive(self):
        """Test that memory usage is a positive integer."""
        usage = get_current_memory_usage_bytes()
        assert isinstance(usage, int)
        assert usage >= 0

    def test_check_memory_limit_within(self):
        """Test check_memory_limit returns True when under limit."""
        limit = MEMORY_LIMIT_GB * 1024 * 1024 * 1024
        assert check_memory_limit(limit - 1024) is True

    def test_check_memory_limit_exceeded(self):
        """Test check_memory_limit returns False when over limit."""
        limit = MEMORY_LIMIT_GB * 1024 * 1024 * 1024
        assert check_memory_limit(limit + 1024) is False

    def test_format_bytes(self):
        """Test format_bytes converts correctly."""
        gb_val = 1.0 * 1024 * 1024 * 1024
        assert format_bytes(gb_val) == "1.00 GB"
        
        mb_val = 512 * 1024 * 1024
        assert format_bytes(mb_val) == "0.50 GB"

    def test_memory_monitor_context_no_exceed(self):
        """Test that context manager completes without error when under limit."""
        logger = get_logger("test_memory_monitor")
        with memory_monitor_context(logger=logger, limit_gb=MEMORY_LIMIT_GB) as stats:
            # Do a tiny bit of work
            _ = [0] * 1000
            time.sleep(0.2)
        
        # If we get here without MemoryError, it passed
        assert True

    def test_memory_monitor_context_exceed_simulation(self):
        """
        Test that context manager raises MemoryError if limit is set very low.
        We set limit to 1KB which should be immediately exceeded by the process.
        """
        logger = get_logger("test_memory_monitor")
        with pytest.raises(MemoryError):
            with memory_monitor_context(logger=logger, limit_gb=0.000001): # ~1KB
                time.sleep(0.5)
                _ = [0] * 1000000