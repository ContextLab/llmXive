"""
Unit tests for the LoggingMixin class.
"""

import json
import tempfile
from pathlib import Path
import pytest

from src.sim.logging_mixin import LoggingMixin
from src.logging_config import setup_logging, LOG_DIR


class TestableComponent(LoggingMixin):
    """Test component that uses LoggingMixin."""

    def __init__(self, run_id: str):
        super().__init__(run_id)

    def run_step(self, coherence: float, diversity: float, latency: float):
        """Simulate running a step and logging metrics."""
        self.log_step(
            coherence_score=coherence,
            diversity_score=diversity,
            step_latency=latency,
            step_id=1,
            extra_metrics={"component": "testable"}
        )


class TestLoggingMixin:
    """Tests for the LoggingMixin class."""

    @pytest.fixture
    def temp_log_dir(self):
        """Create a temporary directory for logging tests."""
        original_dir = LOG_DIR
        with tempfile.TemporaryDirectory() as tmpdir:
            import src.sim.logging_mixin
            import src.logging_config
            src.logging_config.LOG_DIR = Path(tmpdir)
            yield Path(tmpdir)
        src.logging_config.LOG_DIR = original_dir

    def test_mixin_initializes_logger(self, temp_log_dir):
        """Test that the mixin initializes the metric logger."""
        component = TestableComponent("test_mixin_init")
        assert component.metric_logger is not None
        assert component.run_id == "test_mixin_init"

    def test_log_step_writes_metrics(self, temp_log_dir):
        """Test that log_step writes metrics to file."""
        component = TestableComponent("test_mixin_step")
        component.run_step(0.88, 0.76, 0.042)

        metrics_file = temp_log_dir / "test_mixin_step_metrics.jsonl"
        assert metrics_file.exists()

        with open(metrics_file, 'r') as f:
            record = json.loads(f.readline())

        assert record['coherence_score'] == 0.88
        assert record['diversity_score'] == 0.76
        assert record['step_latency'] == 0.042
        assert record['component'] == 'testable'

    def test_log_run_summary(self, temp_log_dir):
        """Test that log_run_summary writes a summary."""
        component = TestableComponent("test_mixin_summary")
        component.log_run_summary(
            total_steps=50,
            avg_coherence=0.85,
            avg_diversity=0.78,
            avg_latency=0.045,
            status="completed"
        )

        metrics_file = temp_log_dir / "test_mixin_summary_metrics.jsonl"

        with open(metrics_file, 'r') as f:
            line = f.readline()
            record = json.loads(line)

        assert 'summary' in record
        assert record['summary']['total_steps'] == 50
        assert record['summary']['status'] == "completed"
