"""
Unit tests for generation retry logic (T020).

Verifies that:
1. Retry logic attempts the configured number of times.
2. Failures are logged correctly to the failure log.
3. Success stops the retry loop immediately.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from generation.diffusion_runner import (
    GenerationFailureLogger,
    MAX_GENERATION_ATTEMPTS
)

class TestGenerationFailureLogger:
    def test_initialization_creates_file(self, tmp_path):
        log_path = tmp_path / "failures.json"
        logger = GenerationFailureLogger(log_path)
        
        assert log_path.exists()
        with open(log_path, 'r') as f:
            data = json.load(f)
            assert "failures" in data
            assert data["failures"] == []

    def test_log_failure_appends_record(self, tmp_path):
        log_path = tmp_path / "failures.json"
        logger = GenerationFailureLogger(log_path)
        
        logger.log_failure("scene_001", "Baseline", 1, "Test error")
        logger.log_failure("scene_001", "Baseline", 2, "Test error 2")
        
        assert logger.get_failure_count() == 2
        
        with open(log_path, 'r') as f:
            data = json.load(f)
            assert len(data["failures"]) == 2
            assert data["failures"][0]["scene_id"] == "scene_001"
            assert data["failures"][0]["attempt"] == 1
            assert data["failures"][1]["attempt"] == 2

    def test_load_existing_log(self, tmp_path):
        log_path = tmp_path / "failures.json"
        existing_data = {
            "failures": [
                {"scene_id": "old_scene", "group": "Baseline", "attempt": 1, "error": "Old"}
            ]
        }
        with open(log_path, 'w') as f:
            json.dump(existing_data, f)
        
        logger = GenerationFailureLogger(log_path)
        
        assert logger.get_failure_count() == 1
        assert logger.failures[0]["scene_id"] == "old_scene"

class TestRetryLogicIntegration:
    @patch('generation.diffusion_runner.generate_single_image')
    @patch('generation.diffusion_runner.load_model')
    def test_retry_on_failure_then_success(self, mock_load, mock_gen, tmp_path):
        # Setup mocks
        mock_pipe = MagicMock()
        mock_load.return_value = (mock_pipe, MagicMock())
        
        # Fail twice, succeed on 3rd
        mock_gen.side_effect = [False, False, True]
        
        from generation.diffusion_runner import run_generation_pipeline
        
        scenes = [{"scene_id": "test_scene_001"}]
        physics_dir = tmp_path / "physics"
        physics_dir.mkdir()
        output_dir = tmp_path / "output"
        failure_log = tmp_path / "failures.json"
        
        stats = run_generation_pipeline(
            scenes, physics_dir, output_dir, failure_log
        )
        
        # Should have called generate 3 times (2 fails, 1 success)
        assert mock_gen.call_count == 3
        # Should succeed on the 3rd attempt
        assert stats["baseline_success"] == 1
        assert stats["failures"] == 0

    @patch('generation.diffusion_runner.generate_single_image')
    @patch('generation.diffusion_runner.load_model')
    def test_max_attempts_exceeded_logs_failure(self, mock_load, mock_gen, tmp_path):
        # Setup mocks
        mock_pipe = MagicMock()
        mock_load.return_value = (mock_pipe, MagicMock())
        
        # Fail every time
        mock_gen.return_value = False
        
        from generation.diffusion_runner import run_generation_pipeline
        
        scenes = [{"scene_id": "test_scene_fail"}]
        physics_dir = tmp_path / "physics"
        physics_dir.mkdir()
        output_dir = tmp_path / "output"
        failure_log = tmp_path / "failures.json"
        
        stats = run_generation_pipeline(
            scenes, physics_dir, output_dir, failure_log
        )
        
        # Should have called generate MAX_GENERATION_ATTEMPTS times
        assert mock_gen.call_count == MAX_GENERATION_ATTEMPTS
        # Should be counted as a failure
        assert stats["failures"] == 1
        
        # Verify log file content
        assert failure_log.exists()
        with open(failure_log, 'r') as f:
            data = json.load(f)
            assert len(data["failures"]) == 1
            assert data["failures"][0]["scene_id"] == "test_scene_fail"
            assert data["failures"][0]["attempt"] == MAX_GENERATION_ATTEMPTS
            assert data["failures"][0]["group"] == "Baseline"