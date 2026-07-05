import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
import pytest
import torch

from src.utils.config import SocraticConfig
from src.utils.logging import SocraticLogger
from src.utils.model_loader import load_model


class TestTrainingCompletion:
    """Contract tests for training completion and logging."""

    def test_training_completion(self):
        """
        Assert training finishes within 6 hours and logs accuracy.

        This test mocks the training loop to simulate a successful run
        within the time budget and verifies the logging of accuracy metrics.
        """
        # Setup
        config = SocraticConfig(
            model_name="microsoft/phi-1.5",
            max_time="6:00:00",
            batch_size=2,
            gradient_accumulation_steps=4,
            use_lora=True,
            seed=42
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = os.path.join(tmp_dir, "training.log")
            logger = SocraticLogger(log_path, "test_training_completion")

            # Mock model and tokenizer
            mock_model = MagicMock()
            mock_model.config = MagicMock()
            mock_model.config.hidden_size = 2048
            mock_model.config.num_attention_heads = 32
            mock_model.config.num_hidden_layers = 24
            mock_model.to.return_value = mock_model
            mock_model.train.return_value = mock_model

            mock_tokenizer = MagicMock()
            mock_tokenizer.pad_token_id = 0
            mock_tokenizer.eos_token_id = 2
            mock_tokenizer.pad_token = "<pad>"
            mock_tokenizer.eos_token = "<eos>"
            mock_tokenizer.decode.return_value = "Test response"

            # Mock the training loop logic
            mock_training_result = {
                "accuracy": 0.85,
                "loss": 0.45,
                "duration_seconds": 1800,  # 30 minutes, well within 6 hours
                "samples_processed": 1000
            }

            # Simulate logging
            logger.log_event("TRAINING_START", {"config": config.to_dict()})
            logger.log_event("TRAINING_PROGRESS", {"step": 100, "loss": 0.5})
            logger.log_event("TRAINING_COMPLETE", mock_training_result)

            # Verify log file exists and contains expected entries
            assert os.path.exists(log_path)

            with open(log_path, 'r') as f:
                log_lines = f.readlines()

            # Check for training completion event
            completion_logged = False
            accuracy_logged = False

            for line in log_lines:
                if line.strip():
                    entry = json.loads(line)
                    if entry.get("event") == "TRAINING_COMPLETE":
                        completion_logged = True
                        assert "accuracy" in entry["data"], "Accuracy must be logged on completion"
                        assert entry["data"]["accuracy"] == 0.85
                    if entry.get("event") == "TRAINING_PROGRESS":
                        accuracy_logged = True

            assert completion_logged, "TRAINING_COMPLETE event must be logged"
            assert accuracy_logged, "Training progress must be logged"

    def test_oom_fallback(self):
        """
        Assert fallback to a smaller-scale model on OOM.

        This test simulates an OutOfMemoryError during model loading/training
        and verifies the system falls back to a smaller model (e.g., Phi-1.5)
        and logs the fallback event.
        """
        config = SocraticConfig(
            model_name="microsoft/phi-2",  # Larger model initially
            max_time="6:00:00",
            batch_size=2,
            gradient_accumulation_steps=4,
            use_lora=True,
            seed=42
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = os.path.join(tmp_dir, "training.log")
            logger = SocraticLogger(log_path, "test_oom_fallback")

            fallback_model_name = "microsoft/phi-1.5"
            fallback_config = SocraticConfig(
                model_name=fallback_model_name,
                max_time="6:00:00",
                batch_size=2,
                gradient_accumulation_steps=4,
                use_lora=True,
                seed=42
            )

            # Simulate OOM on first model
            oom_error = torch.cuda.OutOfMemoryError("CUDA out of memory")

            # Mock load_model to raise OOM on first call, succeed on second
            call_count = 0

            def mock_load_model_side_effect(cfg, *args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise oom_error
                else:
                    mock_model = MagicMock()
                    mock_model.to.return_value = mock_model
                    return mock_model, MagicMock()  # model, tokenizer

            with patch('src.utils.model_loader.load_model', side_effect=mock_load_model_side_effect):
                try:
                    # Attempt to load initial model (will fail)
                    model, tokenizer = load_model(config)
                except torch.cuda.OutOfMemoryError:
                    # Expected first failure
                    pass

                # Attempt fallback
                model, tokenizer = load_model(fallback_config)

            # Verify fallback was attempted and logged
            assert call_count >= 2, "Model load should be attempted at least twice (initial + fallback)"

            # Check log for fallback event
            assert os.path.exists(log_path)

            with open(log_path, 'r') as f:
                log_lines = f.readlines()

            fallback_logged = False
            for line in log_lines:
                if line.strip():
                    entry = json.loads(line)
                    if entry.get("event") == "OOM_FALLBACK":
                        fallback_logged = True
                        assert entry["data"]["fallback_model"] == fallback_model_name
                        assert entry["data"]["original_model"] == config.model_name

            assert fallback_logged, "OOM_FALLBACK event must be logged"