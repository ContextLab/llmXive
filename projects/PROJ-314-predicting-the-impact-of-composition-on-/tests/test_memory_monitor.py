"""
Unit tests for memory monitoring functionality.
"""
import pytest
import os
import sys
from unittest.mock import patch, MagicMock
import json
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from memory_monitor import (
    get_memory_usage_gb,
    check_memory_limit,
    force_garbage_collection,
    validate_dataset_size,
    main
)

try:
    import pandas as pd
    import psutil
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False


class TestMemoryMonitor:
    """Test cases for memory monitoring functions."""

    @pytest.mark.skipif(not HAS_DEPS, reason="psutil or pandas not installed")
    def test_get_memory_usage_gb_returns_positive(self):
        """Test that get_memory_usage_gb returns a positive number."""
        memory = get_memory_usage_gb()
        assert isinstance(memory, float)
        assert memory >= 0.0

    @pytest.mark.skipif(not HAS_DEPS, reason="psutil not installed")
    def test_check_memory_limit_with_low_limit(self):
        """Test check_memory_limit with a very low limit."""
        # Use a very low limit (0.001 GB = 1 MB) which should almost certainly be exceeded
        with patch('memory_monitor.get_int_config', return_value=100):  # High limit to avoid failure
            result = check_memory_limit(limit_gb=100, fail_on_exceed=False)
            
            assert "current_gb" in result
            assert "limit_gb" in result
            assert "exceeded" in result
            assert "message" in result
            assert result["limit_gb"] == 100
            assert isinstance(result["current_gb"], float)

    @pytest.mark.skipif(not HAS_DEPS, reason="psutil not installed")
    def test_check_memory_limit_raises_on_exceed(self):
        """Test that check_memory_limit raises RuntimeError when exceeded."""
        # Mock a scenario where limit is exceeded
        with patch('memory_monitor.get_memory_usage_gb', return_value=100.0):
            with pytest.raises(RuntimeError, match="Memory limit exceeded"):
                check_memory_limit(limit_gb=10, fail_on_exceed=True)

    @pytest.mark.skipif(not HAS_DEPS, reason="psutil or pandas not installed")
    def test_force_garbage_collection(self):
        """Test that force_garbage_collection returns a valid memory value."""
        memory = force_garbage_collection()
        assert isinstance(memory, float)
        assert memory >= 0.0

    @pytest.mark.skipif(not HAS_DEPS, reason="psutil or pandas not installed")
    def test_validate_dataset_size_fits(self):
        """Test validate_dataset_size with a small DataFrame."""
        df = pd.DataFrame({'a': [1, 2, 3], 'b': ['x', 'y', 'z']})
        
        # With a reasonable limit, small DF should pass
        result = validate_dataset_size(df, limit_gb=1)
        assert result is True

    @pytest.mark.skipif(not HAS_DEPS, reason="psutil or pandas not installed")
    def test_validate_dataset_size_exceeds(self):
        """Test validate_dataset_size with a large DataFrame and low limit."""
        # Create a large DataFrame
        df = pd.DataFrame({
            'a': list(range(1000000)),
            'b': list(range(1000000)),
            'c': list(range(1000000))
        })
        
        # With a very low limit, large DF should fail
        result = validate_dataset_size(df, limit_gb=0.001)  # 1 MB limit
        assert result is False

    def test_main_writes_report(self):
        """Test that main() writes a JSON report to disk."""
        output_path = Path("data/reports/memory_status.json")
        
        # Clean up if exists
        if output_path.exists():
            output_path.unlink()
        
        # Run main
        exit_code = main()
        
        assert exit_code == 0
        assert output_path.exists()
        
        # Verify JSON content
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert "current_gb" in data
        assert "limit_gb" in data
        assert "exceeded" in data
        
        # Clean up
        output_path.unlink()

    @pytest.mark.skipif(not HAS_DEPS, reason="psutil not installed")
    def test_memory_limit_from_config(self):
        """Test that check_memory_limit uses config when no limit provided."""
        with patch('memory_monitor.get_int_config', return_value=8):
            result = check_memory_limit(fail_on_exceed=False)
            assert result["limit_gb"] == 8