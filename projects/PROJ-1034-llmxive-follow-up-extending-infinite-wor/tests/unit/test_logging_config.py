"""
Unit tests for logging infrastructure (T010).

Tests verify that:
1. MetricLogger correctly records coherence_score, diversity_score, step_latency
2. Logs are written to the correct file path
3. JSON format is valid and contains required fields
4. Logging occurs at specified intervals
5. Final summary is properly recorded
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from logging_config import MetricLogger, JsonFormatter, get_metric_logger


class TestMetricLogger:
    """Tests for the MetricLogger class."""
    
    def test_logger_initialization(self, tmp_path):
        """Test that logger initializes correctly with run_id and interval."""
        with patch('logging_config.LOG_DIR', tmp_path):
            logger = get_metric_logger("test_run", log_interval=50)
            
            assert logger.run_id == "test_run"
            assert logger.log_interval == 50
            assert logger.step_count == 0
            assert logger.log_file.parent == tmp_path
            assert logger.log_file.suffix == ".jsonl"
    
    def test_log_step_records_metrics(self, tmp_path):
        """Test that log_step correctly records metrics."""
        with patch('logging_config.LOG_DIR', tmp_path):
            logger = get_metric_logger("test_run", log_interval=50)
            
            # Log a step with metrics
            logger.log_step(
                step=100,
                coherence_score=0.85,
                diversity_score=0.72,
                step_latency=0.0012
            )
            
            logger.close()
            
            # Verify file was created
            assert logger.log_file.exists()
            
            # Read and verify content
            with open(logger.log_file, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 1
                
                entry = json.loads(lines[0])
                assert entry['step'] == 100
                assert entry['coherence_score'] == 0.85
                assert entry['diversity_score'] == 0.72
                assert entry['step_latency'] == 0.0012
                assert entry['run_id'] == "test_run"
    
    def test_log_step_interval_behavior(self, tmp_path):
        """Test that logging occurs at specified intervals."""
        with patch('logging_config.LOG_DIR', tmp_path):
            logger = get_metric_logger("test_run", log_interval=100)
            
            # Log steps at various intervals
            for step in [50, 100, 150, 200, 250]:
                logger.log_step(
                    step=step,
                    coherence_score=0.8,
                    diversity_score=0.7,
                    step_latency=0.001
                )
            
            logger.close()
            
            # Verify file was created
            assert logger.log_file.exists()
            
            # Read and count entries
            with open(logger.log_file, 'r') as f:
                lines = f.readlines()
                # Should have 5 entries (one for each step)
                assert len(lines) == 5
                
                # Verify each entry has the correct step
                for i, line in enumerate(lines):
                    entry = json.loads(line)
                    expected_step = [50, 100, 150, 200, 250][i]
                    assert entry['step'] == expected_step
    
    def test_log_step_without_metrics(self, tmp_path):
        """Test that logging works even when metrics are None (periodic logging)."""
        with patch('logging_config.LOG_DIR', tmp_path):
            logger = get_metric_logger("test_run", log_interval=100)
            
            # Log a step without metrics (should still log at interval)
            logger.log_step(step=100)
            
            # Log a step at non-interval (should not log if no metrics)
            logger.log_step(step=150)
            
            logger.close()
            
            # Verify file was created
            assert logger.log_file.exists()
            
            # Read and verify content
            with open(logger.log_file, 'r') as f:
                lines = f.readlines()
                # Only step 100 should be logged (at interval)
                assert len(lines) == 1
                
                entry = json.loads(lines[0])
                assert entry['step'] == 100
    
    def test_log_final_summary(self, tmp_path):
        """Test that final summary is correctly recorded."""
        with patch('logging_config.LOG_DIR', tmp_path):
            logger = get_metric_logger("test_run", log_interval=100)
            
            # Log some steps first
            logger.log_step(step=100, coherence_score=0.85, diversity_score=0.72, step_latency=0.0012)
            
            # Log final summary
            logger.log_final_summary(
                total_steps=100,
                total_duration=15.5,
                avg_coherence=0.85,
                avg_diversity=0.72,
                avg_latency=0.0012
            )
            
            logger.close()
            
            # Verify file was created
            assert logger.log_file.exists()
            
            # Read and verify content
            with open(logger.log_file, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 2  # One step + one summary
                
                # Last entry should be the summary
                summary_entry = json.loads(lines[-1])
                assert summary_entry['event'] == 'simulation_complete'
                assert summary_entry['total_steps'] == 100
                assert summary_entry['total_duration_seconds'] == 15.5
                assert summary_entry['avg_coherence_score'] == 0.85
                assert summary_entry['avg_diversity_score'] == 0.72
                assert summary_entry['avg_step_latency_seconds'] == 0.0012
    
    def test_extra_info_inclusion(self, tmp_path):
        """Test that extra_info is correctly included in log entries."""
        with patch('logging_config.LOG_DIR', tmp_path):
            logger = get_metric_logger("test_run", log_interval=100)
            
            extra_data = {
                "model_version": "v1.2.3",
                "config_hash": "abc123",
                "status": "running"
            }
            
            logger.log_step(
                step=100,
                coherence_score=0.85,
                diversity_score=0.72,
                step_latency=0.0012,
                extra_info=extra_data
            )
            
            logger.close()
            
            # Verify file was created
            assert logger.log_file.exists()
            
            # Read and verify content
            with open(logger.log_file, 'r') as f:
                lines = f.readlines()
                entry = json.loads(lines[0])
                
                # Check extra data fields
                assert entry['model_version'] == "v1.2.3"
                assert entry['config_hash'] == "abc123"
                assert entry['status'] == "running"


class TestJsonFormatter:
    """Tests for the JsonFormatter class."""
    
    def test_format_with_metrics(self):
        """Test that formatter correctly outputs metrics as JSON."""
        formatter = JsonFormatter()
        
        # Create a mock log record with metrics
        record = MagicMock()
        record.created = 1234567890.0
        record.levelname = "INFO"
        record.name = "test_logger"
        record.getMessage.return_value = ""
        record.extra = {
            "metrics": {
                "step": 100,
                "coherence_score": 0.85,
                "diversity_score": 0.72,
                "step_latency": 0.0012
            }
        }
        
        output = formatter.format(record)
        parsed = json.loads(output)
        
        assert parsed['step'] == 100
        assert parsed['coherence_score'] == 0.85
        assert parsed['diversity_score'] == 0.72
        assert parsed['step_latency'] == 0.0012
    
    def test_format_with_summary(self):
        """Test that formatter correctly outputs summary as JSON."""
        formatter = JsonFormatter()
        
        # Create a mock log record with summary
        record = MagicMock()
        record.created = 1234567890.0
        record.levelname = "INFO"
        record.name = "test_logger"
        record.getMessage.return_value = ""
        record.extra = {
            "summary": {
                "event": "simulation_complete",
                "total_steps": 1000,
                "total_duration_seconds": 120.5
            }
        }
        
        output = formatter.format(record)
        parsed = json.loads(output)
        
        assert parsed['event'] == 'simulation_complete'
        assert parsed['total_steps'] == 1000
        assert parsed['total_duration_seconds'] == 120.5


class TestGetMetricLogger:
    """Tests for the get_metric_logger factory function."""
    
    def test_returns_metric_logger_instance(self, tmp_path):
        """Test that factory returns correct logger type."""
        with patch('logging_config.LOG_DIR', tmp_path):
            logger = get_metric_logger("test_run", log_interval=50)
            
            assert isinstance(logger, MetricLogger)
            assert logger.run_id == "test_run"
            assert logger.log_interval == 50
    
    def test_default_interval(self, tmp_path):
        """Test that default interval is used when not specified."""
        with patch('logging_config.LOG_DIR', tmp_path):
            logger = get_metric_logger("test_run")
            
            assert logger.log_interval == 100  # Default value
