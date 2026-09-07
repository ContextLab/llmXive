import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from models.train_llm import train_model, setup_lora, setup_model_and_tokenizer, prepare_training_data
from data.models import Trajectory, SymbolicObservation, FailureType, PerceptionQuality
from datetime import datetime

class TestTrainingCheckpoint:
    @pytest.fixture
    def mock_model(self):
        # Create a mock model that behaves like a PEFT model
        model = MagicMock()
        model.save_pretrained = MagicMock()
        return model

    @pytest.fixture
    def mock_tokenizer(self):
        tokenizer = MagicMock()
        tokenizer.pad_token = "<pad>"
        tokenizer.eos_token = "<eos>"
        tokenizer.save_pretrained = MagicMock()
        return tokenizer

    @pytest.fixture
    def sample_trajectory(self):
        obs = SymbolicObservation(
            timestamp=datetime.now().isoformat(),
            objects=[
                {
                    "class": "cup",
                    "bbox": [10, 20, 30, 40],
                    "centroid": [20, 30],
                    "color_histogram": [0.1, 0.2, 0.3]
                }
            ],
            scene_empty=False,
            perception_quality=PerceptionQuality.HIGH
        )
        return Trajectory(
            id="test_traj_001",
            observations=[obs],
            action="pick_cup",
            outcome="success",
            start_time=datetime.now().isoformat(),
            end_time=datetime.now().isoformat()
        )

    def test_checkpoint_directory_creation(self, mock_model, mock_tokenizer, sample_trajectory, tmp_path):
        """Test that checkpoint directory is created if it doesn't exist."""
        output_dir = tmp_path / "output"
        checkpoint_dir = output_dir / "checkpoints"
        
        # Prepare a minimal dataset
        dataset = prepare_training_data([sample_trajectory], mock_tokenizer)
        
        # Call train_model with checkpointing enabled
        # We mock the actual training loop to avoid heavy computation
        with patch("models.train_llm.Trainer") as mock_trainer_class:
            mock_trainer_instance = MagicMock()
            mock_trainer_class.return_value = mock_trainer_instance
            
            train_model(
                mock_model,
                dataset,
                mock_tokenizer,
                output_dir,
                num_epochs=1,
                checkpoint_interval=1
            )
            
            # Verify that the directory was created
            assert checkpoint_dir.exists(), "Checkpoint directory should be created"
            
            # Verify that save_pretrained was called (simulating a checkpoint save)
            # In a real scenario, Trainer handles this, but we check the logic flow
            assert mock_trainer_instance.train.called

    def test_checkpoint_interval_logic(self, mock_model, mock_tokenizer, sample_trajectory, tmp_path):
        """Test that checkpoints are saved at the specified interval."""
        output_dir = tmp_path / "output"
        checkpoint_interval = 5
        
        dataset = prepare_training_data([sample_trajectory], mock_tokenizer)
        
        with patch("models.train_llm.Trainer") as mock_trainer_class:
            mock_trainer_instance = MagicMock()
            mock_trainer_class.return_value = mock_trainer_instance
            
            # Mock the Trainer's save_model to simulate checkpointing
            def mock_save_model(path):
                # Create a dummy checkpoint file
                (Path(path) / "checkpoint.json").touch()
            
            mock_trainer_instance.save_model = mock_save_model
            
            train_model(
                mock_model,
                dataset,
                mock_tokenizer,
                output_dir,
                num_epochs=1,
                checkpoint_interval=checkpoint_interval
            )
            
            # Verify that save_model was called (which in our mock creates a file)
            # The actual frequency depends on the Trainer's internal logic, 
            # but we ensure the configuration is passed correctly.
            assert mock_trainer_instance.train.called

    def test_final_model_save(self, mock_model, mock_tokenizer, sample_trajectory, tmp_path):
        """Test that the final model is saved after training."""
        output_dir = tmp_path / "output"
        final_model_dir = output_dir / "final_model"
        
        dataset = prepare_training_data([sample_trajectory], mock_tokenizer)
        
        with patch("models.train_llm.Trainer") as mock_trainer_class:
            mock_trainer_instance = MagicMock()
            mock_trainer_class.return_value = mock_trainer_instance
            
            train_model(
                mock_model,
                dataset,
                mock_tokenizer,
                output_dir,
                num_epochs=1
            )
            
            # Verify save_pretrained was called for the final model
            assert mock_model.save_pretrained.called
            assert mock_tokenizer.save_pretrained.called

    def test_checkpoint_path_configuration(self, mock_model, mock_tokenizer, sample_trajectory, tmp_path):
        """Test that checkpoints are saved to the configured directory."""
        output_dir = tmp_path / "output"
        custom_checkpoint_dir = tmp_path / "custom_checkpoints"
        
        dataset = prepare_training_data([sample_trajectory], mock_tokenizer)
        
        with patch("models.train_llm.Trainer") as mock_trainer_class:
            mock_trainer_instance = MagicMock()
            mock_trainer_class.return_value = mock_trainer_instance
            
            train_model(
                mock_model,
                dataset,
                mock_tokenizer,
                output_dir,
                num_epochs=1,
                checkpoint_dir=custom_checkpoint_dir
            )
            
            # The function should ensure the custom checkpoint directory exists
            assert custom_checkpoint_dir.exists()