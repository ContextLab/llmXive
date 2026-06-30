"""
Unit tests for src/benchmark/run_task.py (T043).

Tests:
- Argument parsing
- Task loading logic
- Modality addition logic
- Timeout handling (mocked)
- Output generation
"""
import os
import sys
import json
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.benchmark.run_task import (
    load_task_definition,
    load_modality_configs,
    execute_task,
    main
)
from src.models.routing import ModalityRouter
from src.utils.timeout import TimeoutError


class TestRunTaskUtils:
    """Tests for utility functions in run_task.py"""

    def test_load_task_definition_success(self, tmp_path):
        """Test loading a valid task definition."""
        # Create a temporary task_definitions.yaml
        task_file = tmp_path / "task_definitions.yaml"
        tasks = [
            {
                "task_id": "T001",
                "modalities": ["timeseries"],
                "datasets": ["UCI_HAR"],
                "label_column": "activity"
            },
            {
                "task_id": "T002",
                "modalities": ["tabular"],
                "datasets": ["UCI_adult"],
                "label_column": "class"
            }
        ]
        with open(task_file, 'w') as f:
            yaml.dump(tasks, f)

        # Temporarily override the constant
        import src.benchmark.run_task as run_task_module
        original_path = run_task_module.TASK_DEFINITIONS_PATH
        run_task_module.TASK_DEFINITIONS_PATH = task_file

        try:
            task = load_task_definition("T001")
            assert task["task_id"] == "T001"
            assert task["modalities"] == ["timeseries"]
        finally:
            run_task_module.TASK_DEFINITIONS_PATH = original_path

    def test_load_task_definition_not_found(self, tmp_path):
        """Test loading a non-existent task."""
        task_file = tmp_path / "task_definitions.yaml"
        tasks = [{"task_id": "T001", "modalities": []}]
        with open(task_file, 'w') as f:
            yaml.dump(tasks, f)

        import src.benchmark.run_task as run_task_module
        original_path = run_task_module.TASK_DEFINITIONS_PATH
        run_task_module.TASK_DEFINITIONS_PATH = task_file

        try:
            with pytest.raises(ValueError, match="Task ID 'T999' not found"):
                load_task_definition("T999")
        finally:
            run_task_module.TASK_DEFINITIONS_PATH = original_path

    def test_load_modality_configs(self, tmp_path):
        """Test loading modality configurations."""
        # Create config directory
        config_dir = tmp_path / "modalities"
        config_dir.mkdir()
        
        # Create a mock config
        timeseries_cfg = {
            "model_id": "ts_model_1",
            "model_type": "TimeSeries-Transformer",
            "max_memory_gb": 0.5,
            "inference_script": "scripts/ts_infer.py"
        }
        with open(config_dir / "timeseries.yaml", 'w') as f:
            yaml.dump(timeseries_cfg, f)

        # Mock the path
        import src.benchmark.run_task as run_task_module
        original_dir = run_task_module.MODALITIES_CONFIG_DIR
        run_task_module.MODALITIES_CONFIG_DIR = config_dir

        try:
            configs = load_modality_configs(["timeseries"])
            assert "timeseries" in configs
            assert configs["timeseries"]["model_id"] == "ts_model_1"
        finally:
            run_task_module.MODALITIES_CONFIG_DIR = original_dir


class TestExecuteTask:
    """Tests for execute_task function"""

    def test_execute_task_success(self):
        """Test successful task execution."""
        # Mock router
        mock_router = MagicMock(spec=ModalityRouter)
        mock_router.predict.return_value = {
            "prediction": "class_A",
            "modality_contributions": {"timeseries": 0.8}
        }

        task_def = {
            "task_id": "T001",
            "modalities": ["timeseries"]
        }

        result = execute_task("T001", mock_router, task_def, timeout_seconds=10)

        assert result["status"] == "success"
        assert result["prediction"] == "class_A"
        assert "timing" in result
        assert result["timing"] >= 0

    def test_execute_task_timeout(self):
        """Test task execution with timeout."""
        # Mock router to raise TimeoutError
        mock_router = MagicMock(spec=ModalityRouter)
        mock_router.predict.side_effect = TimeoutError("Test timeout")

        task_def = {
            "task_id": "T001",
            "modalities": ["timeseries"]
        }

        result = execute_task("T001", mock_router, task_def, timeout_seconds=1)

        assert result["status"] == "timeout"
        assert result["prediction"] is None
        assert "error" in result
        assert "timeout" in result["error"].lower()

    def test_execute_task_exception(self):
        """Test task execution with unexpected exception."""
        mock_router = MagicMock(spec=ModalityRouter)
        mock_router.predict.side_effect = ValueError("Unexpected error")

        task_def = {
            "task_id": "T001",
            "modalities": ["timeseries"]
        }

        result = execute_task("T001", mock_router, task_def, timeout_seconds=10)

        assert result["status"] == "error"
        assert result["prediction"] is None
        assert "error" in result


class TestMainIntegration:
    """Integration test for main function"""

    @patch('src.benchmark.run_task.setup_logger')
    @patch('src.benchmark.run_task.get_logger')
    @patch('src.benchmark.run_task.ModalityRouter')
    @patch('src.benchmark.run_task.execute_task')
    @patch('src.benchmark.run_task.update_artifact_timestamp')
    def test_main_flow(
        self, 
        mock_update_ts, 
        mock_exec, 
        mock_router_cls, 
        mock_logger, 
        mock_setup
    ):
        """Test the full main flow with mocked dependencies."""
        # Setup mocks
        mock_exec.return_value = {
            "task_id": "T001",
            "prediction": "result",
            "modality_contributions": {},
            "timing": 1.0,
            "status": "success"
        }
        
        mock_router_instance = MagicMock()
        mock_router_cls.return_value = mock_router_instance

        # Create temporary files for task def and config
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Task definitions
            task_file = tmp_path / "task_definitions.yaml"
            with open(task_file, 'w') as f:
                yaml.dump([{"task_id": "T001", "modalities": ["timeseries"]}], f)
            
            # Modality config
            config_dir = tmp_path / "modalities"
            config_dir.mkdir()
            with open(config_dir / "timeseries.yaml", 'w') as f:
                yaml.dump({"model_id": "test"}, f)

            # Patch paths
            import src.benchmark.run_task as run_task_module
            original_task_path = run_task_module.TASK_DEFINITIONS_PATH
            original_config_dir = run_task_module.MODALITIES_CONFIG_DIR
            original_output_path = run_task_module.OUTPUT_PATH

            run_task_module.TASK_DEFINITIONS_PATH = task_file
            run_task_module.MODALITIES_CONFIG_DIR = config_dir
            run_task_module.OUTPUT_PATH = tmp_path / "results"

            try:
                # Run main with args
                with patch.object(sys, 'argv', [
                    'run_task.py', 
                    '--task-id', 'T001',
                    '--timeout', '10'
                ]):
                    main()

                # Verify execution was called
                mock_exec.assert_called_once()
                # Verify output file was created (implicitly via main logic)
                assert (tmp_path / "results" / "task_T001_result.json").exists()
            finally:
                run_task_module.TASK_DEFINITIONS_PATH = original_task_path
                run_task_module.MODALITIES_CONFIG_DIR = original_config_dir
                run_task_module.OUTPUT_PATH = original_output_path