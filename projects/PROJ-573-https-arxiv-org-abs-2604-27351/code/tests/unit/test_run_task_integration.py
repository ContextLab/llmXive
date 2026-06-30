"""
Integration tests for the run_task script functionality.
These tests verify that task definitions are loaded correctly and 
execution flows work as expected without requiring actual model inference.
"""
import os
import sys
import json
import tempfile
import yaml
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.benchmark.run_task import load_task_definition, load_modality_configs, execute_task

class TestRunTaskIntegration:
    """Integration tests for run_task module functions."""

    @pytest.fixture
    def temp_task_definitions(self):
        """Create a temporary task definitions file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            tasks = [
                {
                    "task_id": "T001",
                    "modalities": ["timeseries"],
                    "datasets": ["UCI_HAR"],
                    "label_column": "activity_label",
                    "description": "Test task 1"
                },
                {
                    "task_id": "T002",
                    "modalities": ["tabular", "text"],
                    "datasets": ["UCI_Adult", "DROP"],
                    "label_column": "income",
                    "description": "Test task 2"
                }
            ]
            yaml.dump(tasks, f)
            temp_path = f.name
        yield Path(temp_path)
        os.unlink(temp_path)

    @pytest.fixture
    def temp_modality_configs(self):
        """Create temporary modality configuration files."""
        config_dir = tempfile.mkdtemp()
        
        # Create timeseries config
        with open(os.path.join(config_dir, "timeseries.yaml"), 'w') as f:
            yaml.dump({
                "model_id": "timeseries_transformer",
                "model_type": "timeseries",
                "max_memory_gb": 0.8,
                "inference_script": "src/models/timeseries_model.py"
            }, f)
        
        # Create tabular config
        with open(os.path.join(config_dir, "tabular.yaml"), 'w') as f:
            yaml.dump({
                "model_id": "tabpfn",
                "model_type": "tabular",
                "max_memory_gb": 0.5,
                "inference_script": "src/models/tabular_model.py"
            }, f)
        
        yield Path(config_dir)
        import shutil
        shutil.rmtree(config_dir)

    def test_load_task_definition_found(self, temp_task_definitions):
        """Test loading an existing task definition."""
        task_def = load_task_definition("T001", temp_task_definitions)
        assert task_def is not None
        assert task_def["task_id"] == "T001"
        assert "timeseries" in task_def["modalities"]

    def test_load_task_definition_not_found(self, temp_task_definitions):
        """Test loading a non-existent task definition raises error."""
        with pytest.raises(KeyError, match="Task definition not found for ID: T999"):
            load_task_definition("T999", temp_task_definitions)

    def test_load_task_definition_file_not_found(self):
        """Test loading from a non-existent file raises error."""
        fake_path = Path("/nonexistent/path.yaml")
        with pytest.raises(FileNotFoundError):
            load_task_definition("T001", fake_path)

    def test_load_modality_configs_success(self, temp_modality_configs):
        """Test loading modality configurations successfully."""
        modalities = ["timeseries", "tabular"]
        configs = load_modality_configs(temp_modality_configs, modalities)
        
        assert "timeseries" in configs
        assert "tabular" in configs
        assert configs["timeseries"]["model_id"] == "timeseries_transformer"
        assert configs["tabular"]["model_id"] == "tabpfn"

    def test_load_modality_configs_partial_missing(self, temp_modality_configs):
        """Test loading when some modality configs are missing."""
        modalities = ["timeseries", "tabular", "image"]
        configs = load_modality_configs(temp_modality_configs, modalities)
        
        assert "timeseries" in configs
        assert "tabular" in configs
        assert "image" in configs  # Should create default config
        assert configs["image"]["model_type"] == "image"

    @patch('src.benchmark.run_task.ModalityRouter')
    def test_execute_task_success(self, mock_router_class, temp_task_definitions, temp_modality_configs):
        """Test successful task execution."""
        # Setup mock
        mock_router = MagicMock()
        mock_router.predict.return_value = {
            "prediction": "walking",
            "contributions": {
                "timeseries": 0.9,
                "tabular": 0.1
            }
        }
        mock_router_class.return_value = mock_router

        task_def = load_task_definition("T001", temp_task_definitions)
        modalities = task_def["modalities"]
        configs = load_modality_configs(temp_modality_configs, modalities)

        result = execute_task(task_def, configs)

        assert result["status"] == "success"
        assert result["task_id"] == "T001"
        assert result["prediction"] == "walking"
        assert "timing" in result
        assert "total_task_time" in result["timing"]

    @patch('src.benchmark.run_task.ModalityRouter')
    def test_execute_task_with_additional_modality(self, mock_router_class, temp_task_definitions, temp_modality_configs):
        """Test task execution with an additional modality."""
        mock_router = MagicMock()
        mock_router.predict.return_value = {
            "prediction": "walking",
            "contributions": {
                "timeseries": 0.8,
                "image": 0.2
            }
        }
        mock_router_class.return_value = mock_router

        task_def = load_task_definition("T001", temp_task_definitions)
        modalities = task_def["modalities"]
        configs = load_modality_configs(temp_modality_configs, modalities)

        result = execute_task(task_def, configs, additional_modality="image")

        assert result["status"] == "success"
        assert "image" in result["config"]["modalities_used"]

    @patch('src.benchmark.run_task.ModalityRouter')
    def test_execute_task_failure_handling(self, mock_router_class, temp_task_definitions, temp_modality_configs):
        """Test task execution when prediction fails."""
        mock_router = MagicMock()
        mock_router.predict.side_effect = Exception("Model inference failed")
        mock_router_class.return_value = mock_router

        task_def = load_task_definition("T001", temp_task_definitions)
        modalities = task_def["modalities"]
        configs = load_modality_configs(temp_modality_configs, modalities)

        result = execute_task(task_def, configs)

        assert result["status"] == "failed"
        assert "error" in result
        assert "Model inference failed" in result["error"]
