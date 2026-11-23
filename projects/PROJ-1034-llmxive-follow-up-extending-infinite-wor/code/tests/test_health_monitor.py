import pytest
import numpy as np
import json
import os
import tempfile
from datetime import datetime
from unittest.mock import patch, MagicMock

from sim.health_monitor import HealthMonitor, validate_metrics_file
from sim.logging_config import SimulationLogger, create_logger

class TestHealthMonitor:
    def test_init(self):
        monitor = HealthMonitor()
        assert monitor.memory_threshold_mb == 6000.0
        assert monitor.value_threshold == 1e10
        assert len(monitor.warnings) == 0

    def test_check_metrics_no_nan(self):
        monitor = HealthMonitor()
        metrics = {
            "coherence": 0.95,
            "diversity": 0.5,
            "nested": {"latency": 0.01}
        }
        found, paths = monitor.check_metrics_for_nan(metrics)
        assert found is False
        assert len(paths) == 0

    def test_check_metrics_nan_detected(self):
        monitor = HealthMonitor()
        metrics = {
            "coherence": float('nan'),
            "diversity": 0.5
        }
        found, paths = monitor.check_metrics_for_nan(metrics)
        assert found is True
        assert "coherence" in paths

    def test_check_metrics_inf_detected(self):
        monitor = HealthMonitor()
        metrics = {
            "coherence": float('inf'),
            "diversity": 0.5
        }
        found, paths = monitor.check_metrics_for_nan(metrics)
        assert found is True
        assert "coherence" in paths

    def test_check_state_explosion_memory(self):
        monitor = HealthMonitor(memory_threshold_mb=500.0)
        metrics = {"val": 1.0}
        is_exploded, msg = monitor.check_state_explosion(metrics, memory_mb=600.0)
        assert is_exploded is True
        assert "Memory explosion" in msg

    def test_check_state_explosion_value(self):
        monitor = HealthMonitor(value_threshold=100.0)
        metrics = {"val": 200.0}
        is_exploded, msg = monitor.check_state_explosion(metrics)
        assert is_exploded is True
        assert "Value explosion" in msg

    def test_record_warning(self):
        monitor = HealthMonitor()
        monitor.record_warning("TEST", "Test message", step=10)
        assert len(monitor.warnings) == 1
        assert monitor.warnings[0]["type"] == "TEST"
        assert monitor.warnings[0]["step"] == 10

class TestValidateMetricsFile:
    def test_validate_file_not_found(self):
        result = validate_metrics_file("nonexistent.json")
        assert "error" in result

    def test_validate_empty_file(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write("")
            path = f.name
        try:
            result = validate_metrics_file(path)
            assert result["total_lines"] == 0
        finally:
            os.unlink(path)

    def test_validate_json_with_nan(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            f.write(json.dumps({"metrics": {"coherence": float('nan')}}) + '\n')
            f.write(json.dumps({"metrics": {"coherence": 0.9}}) + '\n')
            path = f.name
        try:
            result = validate_metrics_file(path)
            assert result["nan_lines"] == 1
            assert result["total_lines"] == 2
        finally:
            os.unlink(path)

    def test_validate_json_with_explosion(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            f.write(json.dumps({"metrics": {"val": 1e15}}) + '\n')
            path = f.name
        try:
            result = validate_metrics_file(path)
            assert result["explosion_lines"] == 1
        finally:
            os.unlink(path)

class TestLoggingIntegration:
    def test_logger_handles_nan_gracefully(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            path = f.name
        
        try:
            logger = create_logger(path)
            
            # Log a valid step
            valid = logger.log_step(0, {"coherence_score": 0.9, "diversity_score": 0.5, "step_latency": 0.01}, 100.0)
            assert valid is True
            
            # Log a step with NaN
            invalid = logger.log_step(1, {"coherence_score": float('nan'), "diversity_score": 0.5, "step_latency": 0.01}, 100.0)
            assert invalid is False
            
            logger.close()
            
            # Verify file was written and contains the invalid step (with NaN or flagged)
            with open(path, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 2
                
                # Check the second line for the warning
                data = json.loads(lines[1])
                assert data["step"] == 1
                assert data["is_valid"] is False
                assert len(data["warnings"]) > 0
        finally:
            os.unlink(path)

    def test_logger_handles_explosion_gracefully(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            path = f.name
        
        try:
            logger = create_logger(path)
            
            # Log a step with explosion
            invalid = logger.log_step(0, {"coherence_score": 1e15, "diversity_score": 0.5, "step_latency": 0.01}, 100.0)
            assert invalid is False
            
            logger.close()
            
            with open(path, 'r') as f:
                lines = f.readlines()
                data = json.loads(lines[0])
                assert data["is_valid"] is False
                assert len(data["warnings"]) > 0
        finally:
            os.unlink(path)
