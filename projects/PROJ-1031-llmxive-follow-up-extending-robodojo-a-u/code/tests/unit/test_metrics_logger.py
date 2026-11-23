"""
Unit tests for metrics logging and resource limits.
"""
import pytest
import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure src is importable
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.metrics_logger import MetricsLogger, TaskMetrics, ResourceLimitExceeded


class TestMetricsLogger:
    """Tests for MetricsLogger functionality."""

    def test_logger_initialization(self):
        """Verify MetricsLogger initializes."""
        logger = MetricsLogger()
        assert logger is not None

    def test_task_metrics_structure(self):
        """Verify TaskMetrics dataclass structure."""
        metrics = TaskMetrics(
            task_id="test_001",
            cpu_cycles=1000,
            ram_mb=500,
            wall_time=1.5
        )
        assert metrics.task_id == "test_001"
        assert metrics.ram_mb == 500

    @patch('src.metrics_logger.tracemalloc')
    def test_resource_limit_exceeded(self, mock_tracemalloc):
        """Verify ResourceLimitExceeded is raised when RAM limit is hit."""
        # Mock current memory to be high
        mock_tracemalloc.get_traced_memory.return_value = (10 * 1024 * 1024 * 1024, 0) # 10GB

        logger = MetricsLogger()
        with pytest.raises(ResourceLimitExceeded):
            logger.check_resource_limits()
