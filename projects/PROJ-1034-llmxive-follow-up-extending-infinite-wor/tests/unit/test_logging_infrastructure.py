"""
Unit tests for logging infrastructure (T010).

Tests verify that coherence_score, diversity_score, and step_latency
are correctly recorded at intervals.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from logging_config import create_metrics_logger, SimulationMetricsLogger

class TestSimulationMetricsLogger:
    """Tests for the SimulationMetricsLogger class."""
    
    def test_initialization(self):
        """Test logger can be initialized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test_metrics.json")
            logger = create_metrics_logger(log_file=log_file)
            
            assert logger is not None
            assert isinstance(logger, SimulationMetricsLogger)
    
    def test_log_step_metrics(self):
        """Test that step metrics are logged correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test_metrics.json")
            logger = create_metrics_logger(log_file=log_file)
            
            # Log a step
            logger.log_step_metrics(
                step=1,
                coherence_score=0.85,
                diversity_score=0.72,
                step_latency=0.045
            )
            
            # Verify buffer has the record
            assert len(logger._metrics_buffer) == 1
            record = logger._metrics_buffer[0]
            
            assert record["step"] == 1
            assert abs(record["coherence_score"] - 0.85) < 0.001
            assert abs(record["diversity_score"] - 0.72) < 0.001
            assert abs(record["step_latency"] - 0.045) < 0.001
            assert "timestamp" in record
    
    def test_flush_buffer_creates_file(self):
        """Test that flush_buffer creates the output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test_metrics.json")
            logger = create_metrics_logger(log_file=log_file)
            
            logger.log_step_metrics(
                step=1,
                coherence_score=0.85,
                diversity_score=0.72,
                step_latency=0.045
            )
            
            logger.flush_buffer()
            
            assert os.path.exists(log_file)
    
    def test_flush_buffer_writes_json(self):
        """Test that flush_buffer writes valid JSON lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test_metrics.json")
            logger = create_metrics_logger(log_file=log_file)
            
            logger.log_step_metrics(
                step=1,
                coherence_score=0.85,
                diversity_score=0.72,
                step_latency=0.045
            )
            logger.log_step_metrics(
                step=2,
                coherence_score=0.88,
                diversity_score=0.75,
                step_latency=0.052
            )
            
            logger.flush_buffer()
            
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) == 2
            
            # Verify each line is valid JSON
            for line in lines:
                record = json.loads(line.strip())
                assert "step" in record
                assert "coherence_score" in record
                assert "diversity_score" in record
                assert "step_latency" in record
    
    def test_multiple_flushes_append(self):
        """Test that multiple flushes append to the file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test_metrics.json")
            logger = create_metrics_logger(log_file=log_file)
            
            # First batch
            logger.log_step_metrics(step=1, coherence_score=0.8, diversity_score=0.7, step_latency=0.04)
            logger.flush_buffer()
            
            # Second batch
            logger.log_step_metrics(step=2, coherence_score=0.85, diversity_score=0.75, step_latency=0.045)
            logger.flush_buffer()
            
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) == 2
    
    def test_additional_metrics_included(self):
        """Test that additional metrics are included in the log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test_metrics.json")
            logger = create_metrics_logger(log_file=log_file)
            
            logger.log_step_metrics(
                step=1,
                coherence_score=0.85,
                diversity_score=0.72,
                step_latency=0.045,
                additional_metrics={"extra_metric": 42, "flag": True}
            )
            
            logger.flush_buffer()
            
            with open(log_file, 'r') as f:
                record = json.loads(f.readline().strip())
            
            assert record["extra_metric"] == 42
            assert record["flag"] is True
    
    def test_interval_logging_simulation(self):
        """Test logging at regular intervals as per T010 requirement."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test_metrics.json")
            logger = create_metrics_logger(log_file=log_file)
            
            # Simulate logging every 5 steps
            interval = 5
            total_steps = 20
            
            logged_steps = []
            for step in range(1, total_steps + 1):
                # Only log at intervals
                if step % interval == 0:
                    logger.log_step_metrics(
                        step=step,
                        coherence_score=0.8 + (step * 0.01),
                        diversity_score=0.7 + (step * 0.01),
                        step_latency=0.04 + (step * 0.001)
                    )
                    logged_steps.append(step)
            
            logger.flush_buffer()
            
            # Verify only interval steps were logged
            assert logged_steps == [5, 10, 15, 20]
            
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) == 4
            
            # Verify content
            for i, line in enumerate(lines):
                record = json.loads(line.strip())
                expected_step = (i + 1) * 5
                assert record["step"] == expected_step