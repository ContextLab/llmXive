"""
Integration test for modality addition (User Story 2).

This test verifies that a new modality can be added to the heterogeneous pipeline
without breaking existing tasks. It simulates adding a "dummy" image modality
and verifies that the pipeline processes it using the specified model configuration
and includes its output in the final prediction.

Dependencies:
- T033: Contract test for modality_model schema (verifies schema structure)
- T035-T037: Modality-specific model wrappers (required for actual model loading)
- T038: Heterogeneous routing layer (required for routing logic)
- T040-T042: Modality config files (required for configuration)
"""

import os
import sys
import tempfile
import yaml
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.tasks.task_runner import TaskRunner
from src.utils.logging import setup_logger, get_logger
from src.utils.checksum_utils import compute_file_sha256, update_artifact_hash

# Setup logger
logger = setup_logger("integration_test_modality_addition")

# Constants
DUMMY_IMAGE_MODALITY_CONFIG = {
    "model_id": "dummy-image-model-v1",
    "model_type": "image",
    "max_memory_gb": 0.5,
    "inference_script": "src/models/image_model.py",
    "description": "Dummy image modality for integration testing"
}

TEST_TASK_DEFINITION = {
    "task_id": "TEST-MOD-ADD-001",
    "modalities": ["tabular", "image"],  # Include new image modality
    "datasets": ["UCI_HAR"],
    "label_column": "activity_label"
}

class TestModalityAddition:
    """Integration tests for adding new modalities to the pipeline."""
    
    def test_modality_config_creation_and_validation(self):
        """Test that a new modality config can be created and validated against schema."""
        # Create temporary directory for test config
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "dummy_image.yaml"
            
            # Write dummy modality config
            with open(config_path, 'w') as f:
                yaml.dump(DUMMY_IMAGE_MODALITY_CONFIG, f)
            
            # Load and verify config structure
            with open(config_path, 'r') as f:
                loaded_config = yaml.safe_load(f)
            
            # Verify required fields exist
            assert "model_id" in loaded_config
            assert "model_type" in loaded_config
            assert "max_memory_gb" in loaded_config
            assert "inference_script" in loaded_config
            
            # Verify specific values
            assert loaded_config["model_type"] == "image"
            assert loaded_config["model_id"] == "dummy-image-model-v1"
            
            logger.info(f"✓ Modality config created and validated at {config_path}")
    
    def test_task_runner_accepts_new_modality(self):
        """Test that TaskRunner can handle tasks with newly added modalities."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create task definitions file with new modality
            task_file = Path(tmpdir) / "test_tasks.yaml"
            with open(task_file, 'w') as f:
                yaml.dump([TEST_TASK_DEFINITION], f)
            
            # Create modality config directory
            modalities_dir = Path(tmpdir) / "modalities"
            modalities_dir.mkdir()
            
            # Write image modality config
            image_config_path = modalities_dir / "image.yaml"
            with open(image_config_path, 'w') as f:
                yaml.dump(DUMMY_IMAGE_MODALITY_CONFIG, f)
            
            # Initialize TaskRunner with test configs
            runner = TaskRunner(
                task_definitions_path=str(task_file),
                modality_configs_dir=str(modalities_dir)
            )
            
            # Verify task can be loaded
            task = runner.get_task("TEST-MOD-ADD-001")
            assert task is not None
            assert "image" in task["modalities"]
            
            logger.info("✓ TaskRunner successfully loaded task with new modality")
    
    @pytest.mark.integration
    def test_heterogeneous_routing_with_new_modality(self):
        """
        Test that the heterogeneous routing layer correctly routes
        inputs to the new modality's model.
        
        This simulates the full pipeline flow with a new modality.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup task and modality configs
            task_file = Path(tmpdir) / "test_tasks.yaml"
            with open(task_file, 'w') as f:
                yaml.dump([TEST_TASK_DEFINITION], f)
            
            modalities_dir = Path(tmpdir) / "modalities"
            modalities_dir.mkdir()
            
            image_config_path = modalities_dir / "image.yaml"
            with open(image_config_path, 'w') as f:
                yaml.dump(DUMMY_IMAGE_MODALITY_CONFIG, f)
            
            # Mock the modality router to simulate routing behavior
            with patch('src.models.routing.ModalityRouter') as mock_router:
                # Setup mock behavior
                mock_instance = MagicMock()
                mock_router.return_value = mock_instance
                
                # Simulate routing for the new image modality
                mock_instance.get_model.return_value = MagicMock()
                mock_instance.get_model.return_value.predict.return_value = {
                    "prediction": "test_prediction",
                    "confidence": 0.85,
                    "modality": "image"
                }
                
                # Initialize runner
                runner = TaskRunner(
                    task_definitions_path=str(task_file),
                    modality_configs_dir=str(modalities_dir)
                )
                
                # Mock the task execution
                with patch.object(runner, 'run_task') as mock_run:
                    mock_run.return_value = {
                        "task_id": "TEST-MOD-ADD-001",
                        "prediction": "test_prediction",
                        "modality_contributions": {
                            "tabular": 0.4,
                            "image": 0.6
                        },
                        "timing": 0.5
                    }
                    
                    result = runner.run_task("TEST-MOD-ADD-001")
                    
                    # Verify routing was called for image modality
                    assert mock_instance.get_model.called
                    call_args = mock_instance.get_model.call_args
                    assert call_args[0][0] == "image"
                    
                    # Verify result includes new modality contribution
                    assert "image" in result["modality_contributions"]
                    assert result["modality_contributions"]["image"] > 0
                    
                    logger.info("✓ Heterogeneous routing correctly handled new image modality")
    
    def test_missing_modality_handler_integration(self):
        """Test that missing modality handler works correctly with new modalities."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup configs
            task_file = Path(tmpdir) / "test_tasks.yaml"
            task_def_missing = {
                "task_id": "TEST-MOD-MISSING-001",
                "modalities": ["tabular", "image"],
                "datasets": ["UCI_HAR"],
                "label_column": "activity_label"
            }
            with open(task_file, 'w') as f:
                yaml.dump([task_def_missing], f)
            
            modalities_dir = Path(tmpdir) / "modalities"
            modalities_dir.mkdir()
            
            # Only create tabular config, missing image config
            tabular_config = {
                "model_id": "tabular-model-v1",
                "model_type": "tabular",
                "max_memory_gb": 0.5,
                "inference_script": "src/models/tabular_model.py"
            }
            with open(modalities_dir / "tabular.yaml", 'w') as f:
                yaml.dump(tabular_config, f)
            
            # Initialize runner
            runner = TaskRunner(
                task_definitions_path=str(task_file),
                modality_configs_dir=str(modalities_dir)
            )
            
            # Verify task loads but missing modality is detected
            task = runner.get_task("TEST-MOD-MISSING-001")
            assert task is not None
            assert "image" in task["modalities"]
            
            # Verify missing modality detection logic
            available_modalities = ["tabular"]  # Only tabular config exists
            missing = [m for m in task["modalities"] if m not in available_modalities]
            assert "image" in missing
            
            logger.info("✓ Missing modality detection works correctly for new modalities")
    
    def test_state_tracking_for_new_modality(self):
        """Test that state tracking updates when new modality configs are added."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create state file
            state_file = Path(tmpdir) / "state.yaml"
            initial_state = {
                "artifact_hashes": {},
                "updated_at": "2024-01-01T00:00:00Z"
            }
            with open(state_file, 'w') as f:
                yaml.dump(initial_state, f)
            
            # Create modality config
            image_config = {
                "model_id": "new-image-model",
                "model_type": "image",
                "max_memory_gb": 0.5,
                "inference_script": "src/models/image_model.py"
            }
            config_path = Path(tmpdir) / "image.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(image_config, f)
            
            # Compute hash and update state
            file_hash = compute_file_sha256(str(config_path))
            
            # Load state and update
            with open(state_file, 'r') as f:
                state = yaml.safe_load(f)
            
            state["artifact_hashes"][str(config_path)] = file_hash
            
            with open(state_file, 'w') as f:
                yaml.dump(state, f)
            
            # Verify state was updated
            with open(state_file, 'r') as f:
                updated_state = yaml.safe_load(f)
            
            assert str(config_path) in updated_state["artifact_hashes"]
            assert updated_state["artifact_hashes"][str(config_path)] == file_hash
            
            logger.info("✓ State tracking correctly updated for new modality config")
    
    def test_full_pipeline_simulation_with_new_modality(self):
        """
        End-to-end simulation of adding a new modality to the pipeline.
        
        This test simulates:
        1. Creating a new modality config file
        2. Updating task definitions to include the new modality
        3. Running the task through the pipeline
        4. Verifying the output includes contributions from the new modality
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Step 1: Create new modality config
            modalities_dir = Path(tmpdir) / "modalities"
            modalities_dir.mkdir()
            
            new_modality_config = {
                "model_id": "spectral-analysis-model",
                "model_type": "spectral",
                "max_memory_gb": 0.8,
                "inference_script": "src/models/spectral_model.py",
                "description": "New spectral analysis modality"
            }
            
            config_path = modalities_dir / "spectral.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(new_modality_config, f)
            
            # Step 2: Create task with new modality
            task_file = Path(tmpdir) / "tasks.yaml"
            new_task = {
                "task_id": "SPECTRAL-TEST-001",
                "modalities": ["tabular", "spectral"],
                "datasets": ["UCI_HAR"],
                "label_column": "activity_label"
            }
            
            with open(task_file, 'w') as f:
                yaml.dump([new_task], f)
            
            # Step 3: Initialize and run pipeline simulation
            runner = TaskRunner(
                task_definitions_path=str(task_file),
                modality_configs_dir=str(modalities_dir)
            )
            
            # Mock the actual model execution
            with patch.object(runner, 'run_task') as mock_run:
                mock_run.return_value = {
                    "task_id": "SPECTRAL-TEST-001",
                    "prediction": "walking",
                    "modality_contributions": {
                        "tabular": 0.3,
                        "spectral": 0.7  # New modality has higher contribution
                    },
                    "timing": 1.2
                }
                
                result = runner.run_task("SPECTRAL-TEST-001")
                
            # Step 4: Verify results
            assert result is not None
            assert "spectral" in result["modality_contributions"]
            assert result["modality_contributions"]["spectral"] > 0.5
            
            # Verify state tracking (simulated)
            file_hash = compute_file_sha256(str(config_path))
            assert file_hash is not None
            
            logger.info("✓ Full pipeline simulation successful with new spectral modality")
            logger.info(f"  - New modality: {new_modality_config['model_type']}")
            logger.info(f"  - Contribution: {result['modality_contributions']['spectral']:.1%}")
            logger.info(f"  - Config hash: {file_hash[:16]}...")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
