import os
import sys
import json
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Ensure code/src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.benchmark.run_task import load_task_definition, load_modality_configs, execute_task, main

class TestRunTaskUtils:
    def test_load_task_definition_not_found(self, tmp_path):
        # Create a temp task file with no matching ID
        task_file = tmp_path / "tasks.yaml"
        task_file.write_text("- task_id: T999\n  modalities: [text]")
        
        with patch("src.benchmark.run_task.TASK_DEFS_PATH", task_file):
            result = load_task_definition("T001")
            assert result is None

    def test_load_task_definition_found(self, tmp_path):
        task_file = tmp_path / "tasks.yaml"
        task_file.write_text("- task_id: T001\n  modalities: [text]\n- task_id: T002\n  modalities: [image]")
        
        with patch("src.benchmark.run_task.TASK_DEFS_PATH", task_file):
            result = load_task_definition("T001")
            assert result is not None
            assert result["task_id"] == "T001"

    def test_load_modality_configs_missing(self, tmp_path):
        # Create empty modalities dir
        modalities_dir = tmp_path / "modalities"
        modalities_dir.mkdir()
        
        with patch("src.benchmark.run_task.MODALITIES_DIR", modalities_dir):
            configs = load_modality_configs(["text", "image"])
            assert len(configs) == 0

    def test_load_modality_configs_found(self, tmp_path):
        modalities_dir = tmp_path / "modalities"
        modalities_dir.mkdir()
        
        # Create a config file
        config_file = modalities_dir / "text.yaml"
        config_file.write_text("model_id: test-model\nmodel_type: transformer")
        
        with patch("src.benchmark.run_task.MODALITIES_DIR", modalities_dir):
            configs = load_modality_configs(["text"])
            assert "text" in configs
            assert configs["text"]["model_id"] == "test-model"

class TestExecuteTask:
    def test_execute_heterogeneous_mode(self):
        task_def = {
            "task_id": "T001",
            "modalities": ["text"],
            "mode": "heterogeneous"
        }
        modality_configs = {
            "text": {"model_id": "test-text-model"}
        }
        
        result = execute_task(task_def, modality_configs, add_modality=None)
        
        assert result["status"] == "success"
        assert result["task_id"] == "T001"
        assert "prediction" in result
        assert "modality_contributions" in result
        assert "timing" in result

    def test_execute_unified_mode(self):
        task_def = {
            "task_id": "T002",
            "modalities": ["text"],
            "mode": "unified"
        }
        modality_configs = {
            "text": {"model_id": "test-text-model"}
        }
        
        result = execute_task(task_def, modality_configs, add_modality=None)
        
        assert result["status"] == "success"
        assert result["mode"] == "unified"
        assert "text_prediction" in result["prediction"]

    def test_execute_with_missing_modality(self):
        task_def = {
            "task_id": "T003",
            "modalities": ["text", "image"],
            "mode": "heterogeneous"
        }
        # Only text config exists
        modality_configs = {
            "text": {"model_id": "test-text-model"}
        }
        
        result = execute_task(task_def, modality_configs, add_modality=None)
        
        assert result["status"] == "success"
        # Image should be marked as placeholder or handled
        assert "image" in result["modality_contributions"]

    def test_execute_with_added_modality(self):
        task_def = {
            "task_id": "T001",
            "modalities": ["text"],
            "mode": "heterogeneous"
        }
        modality_configs = {
            "text": {"model_id": "test-text-model"},
            "image": {"model_id": "test-image-model"}
        }
        
        result = execute_task(task_def, modality_configs, add_modality="image")
        
        assert result["status"] == "success"
        assert "image" in result["modality_contributions"]

class TestMainIntegration:
    @patch("sys.argv", ["run_task.py", "--task-id", "T001"])
    @patch("src.benchmark.run_task.load_task_definition")
    @patch("src.benchmark.run_task.load_modality_configs")
    @patch("src.benchmark.run_task.execute_task")
    def test_main_success(self, mock_exec, mock_load_mod, mock_load_task):
        mock_load_task.return_value = {"task_id": "T001", "modalities": ["text"]}
        mock_load_mod.return_value = {"text": {}}
        mock_exec.return_value = {"status": "success", "task_id": "T001"}
        
        # Capture stdout
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            main()
        
        output = f.getvalue()
        assert "success" in output
        assert "T001" in output

    @patch("sys.argv", ["run_task.py", "--task-id", "T999"])
    @patch("src.benchmark.run_task.load_task_definition")
    def test_main_not_found(self, mock_load_task):
        mock_load_task.return_value = None
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 1