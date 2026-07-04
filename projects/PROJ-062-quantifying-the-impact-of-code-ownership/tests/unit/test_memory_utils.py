"""
Unit tests for memory management utilities.
"""
import gc
import sys
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
from utils.memory_utils import (
    get_current_memory_mb,
    check_memory_limit,
    force_gc,
    clear_memory,
    process_repository_batch,
    memory_limit_decorator,
    MAX_RAM_GB
)


class TestGetCurrentMemoryMb:
    """Tests for get_current_memory_mb function."""

    def test_returns_positive_value(self):
        """Memory usage should always be a positive number."""
        memory = get_current_memory_mb()
        assert isinstance(memory, float)
        assert memory >= 0

    @patch('utils.memory_utils.resource')
    def test_uses_resource_module(self, mock_resource):
        """Should use resource module when available."""
        mock_usage = MagicMock()
        mock_usage.ru_maxrss = 102400  # 100 MB in KB
        mock_resource.getrusage.return_value = mock_usage

        memory = get_current_memory_mb()
        assert memory == 100.0
        mock_resource.getrusage.assert_called_once()


class TestCheckMemoryLimit:
    """Tests for check_memory_limit function."""

    def test_within_limit_returns_true(self):
        """Should return True when memory is within limit."""
        with patch('utils.memory_utils.get_current_memory_mb', return_value=1000.0):
            assert check_memory_limit(limit_mb=2000.0) is True

    def test_exceeds_limit_returns_false(self):
        """Should return False when memory exceeds limit."""
        with patch('utils.memory_utils.get_current_memory_mb', return_value=3000.0):
            assert check_memory_limit(limit_mb=2000.0) is False

    def test_default_limit_is_7gb(self):
        """Default limit should be MAX_RAM_GB (7GB)."""
        expected_limit_mb = MAX_RAM_GB * 1024
        with patch('utils.memory_utils.get_current_memory_mb', return_value=expected_limit_mb - 1):
            assert check_memory_limit() is True

        with patch('utils.memory_utils.get_current_memory_mb', return_value=expected_limit_mb + 1):
            assert check_memory_limit() is False


class TestForceGc:
    """Tests for force_gc function."""

    def test_calls_gc_collect(self):
        """Should call gc.collect()."""
        with patch('utils.memory_utils.gc.collect', return_value=100) as mock_collect:
            result = force_gc()
            assert result == 100
            mock_collect.assert_called_once()


class TestClearMemory:
    """Tests for clear_memory function."""

    def test_clears_memory(self):
        """Should force garbage collection."""
        with patch('utils.memory_utils.force_gc') as mock_gc:
            with patch('utils.memory_utils.get_current_memory_mb', return_value=100.0):
                clear_memory()
                mock_gc.assert_called_once()


class TestProcessRepositoryBatch:
    """Tests for process_repository_batch function."""

    def test_processes_single_repository(self):
        """Should process a single repository and clear memory."""
        def mock_process(repo):
            return f"processed_{repo}"

        repos = [1, 2, 3]

        with patch('utils.memory_utils.clear_memory') as mock_clear:
            with patch('utils.memory_utils.check_memory_limit', return_value=True):
                results = process_repository_batch(iter(repos), mock_process)

        assert len(results) == 3
        assert results == ['processed_1', 'processed_2', 'processed_3']
        # Memory should be cleared after each repository (batch_size=1)
        assert mock_clear.call_count == 3

    def test_handles_processing_error(self):
        """Should raise exception when processing fails."""
        def failing_process(repo):
            if repo == 2:
                raise ValueError("Processing failed")
            return f"processed_{repo}"

        repos = [1, 2, 3]

        with pytest.raises(ValueError, match="Processing failed"):
            with patch('utils.memory_utils.check_memory_limit', return_value=True):
                process_repository_batch(iter(repos), failing_process)

    def test_respects_batch_size(self):
        """Should clear memory after batch_size repositories."""
        def mock_process(repo):
            return f"processed_{repo}"

        repos = [1, 2, 3, 4, 5]

        with patch('utils.memory_utils.clear_memory') as mock_clear:
            with patch('utils.memory_utils.check_memory_limit', return_value=True):
                process_repository_batch(iter(repos), mock_process, batch_size=2)

        # Should clear after repos 2 and 4
        assert mock_clear.call_count == 2


class TestMemoryLimitDecorator:
    """Tests for memory_limit_decorator."""

    def test_decorator_allows_within_limit(self):
        """Should allow function execution when within limit."""
        @memory_limit_decorator(max_gb=1.0)
        def my_func():
            return "success"

        with patch('utils.memory_utils.get_current_memory_mb', return_value=500.0):
            result = my_func()
            assert result == "success"

    def test_decorator_warns_when_exceeds(self, caplog):
        """Should log warning when memory exceeds limit."""
        @memory_limit_decorator(max_gb=0.5)
        def my_func():
            return "success"

        with patch('utils.memory_utils.get_current_memory_mb', return_value=600.0):
            result = my_func()
            assert result == "success"

            # Check that a warning was logged
            assert any("exceeded memory limit" in str(record.message) for record in caplog.records)