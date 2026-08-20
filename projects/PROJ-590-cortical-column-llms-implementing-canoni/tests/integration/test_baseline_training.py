import json
import os
import tempfile
import pytest
from pathlib import Path
import sys
import torch
import torch.nn as nn
import numpy as np
import logging

# Ensure project root is in path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.models.baseline_transformer import create_baseline_transformer
from src.data.benchmarks import generate_training_data, generate_test_data
from src.training.trainer import TrainingConfig, run_training
from src.training.homeostasis import log_gradient_norms, HomeostasisConfig
from src.utils.statistics import load_gradient_norms

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory structure for test outputs."""
    logs_dir = tmp_path / "data" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return tmp_path

class TestBaselineTrainingWithGradientLogging:
    """
    Integration test for T011b:
    Explicitly runs the baseline model with log_gradient_norms enabled
    to populate data/logs/gradient_norms.json for SC-002 verification.
    """

    def test_baseline_training_logs_gradient_norms(self, temp_output_dir):
        """
        Verify that running the baseline training pipeline with gradient
        logging enabled produces a valid gradient_norms.json file.
        """
        # Setup paths relative to temp_output_dir to avoid writing to project root during test
        logs_dir = temp_output_dir / "data" / "logs"
        gradient_log_path = logs_dir / "gradient_norms.json"

        # Ensure directory exists
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Generate synthetic data (Lorenz for training, Polynomials for test)
        logger.info("Generating training data...")
        train_X, train_y = generate_training_data(n_samples=500, sequence_length=20)
        logger.info("Generating test data...")
        test_X, test_y = generate_test_data(n_samples=200, sequence_length=20)

        # Create a minimal baseline transformer
        logger.info("Creating baseline transformer model...")
        model = create_baseline_transformer(
            input_dim=train_X.shape[-1],
            d_model=64,
            nhead=4,
            num_layers=2,
            ff_dim=128,
            dropout=0.1
        )

        # Configure training
        # We use a very short training duration for the integration test
        config = TrainingConfig(
            epochs=2,  # Minimal epochs for integration test
            batch_size=32,
            lr=1e-3,
            device="cpu",
            log_interval=1,
            gradient_clip_value=1.0,
            # Enable gradient logging
            log_gradient_norms=True,
            gradient_log_path=str(gradient_log_path)
        )

        # Run training
        logger.info("Starting training loop with gradient logging...")
        try:
            metrics = run_training(
                model=model,
                train_loader=torch.utils.data.DataLoader(
                    torch.utils.data.TensorDataset(
                        torch.FloatTensor(train_X),
                        torch.FloatTensor(train_y)
                    ),
                    batch_size=config.batch_size,
                    shuffle=True
                ),
                test_loader=torch.utils.data.DataLoader(
                    torch.utils.data.TensorDataset(
                        torch.FloatTensor(test_X),
                        torch.FloatTensor(test_y)
                    ),
                    batch_size=config.batch_size
                ),
                config=config
            )
        except Exception as e:
            logger.error(f"Training failed: {e}")
            raise

        # Verify the output file was created
        assert gradient_log_path.exists(), (
            f"Gradient log file not found at {gradient_log_path}. "
            "The training loop must call log_gradient_norms to create this file."
        )

        # Verify the content is valid JSON and contains expected structure
        with open(gradient_log_path, 'r') as f:
            log_data = json.load(f)

        assert isinstance(log_data, dict), "Gradient log must be a JSON object."
        assert "steps" in log_data, "Gradient log must contain a 'steps' list."
        assert len(log_data["steps"]) > 0, "Gradient log must contain at least one step."

        # Verify structure of a step entry
        first_step = log_data["steps"][0]
        assert "step" in first_step, "Step entry must have 'step' index."
        assert "norms" in first_step, "Step entry must have 'norms' dict."

        # Verify norms contains weight and bias keys (or at least some parameters)
        norms = first_step["norms"]
        assert isinstance(norms, dict), "Norms must be a dictionary."
        assert len(norms) > 0, "Norms dictionary must not be empty."

        logger.info(f"Successfully verified gradient logging. File: {gradient_log_path}")
        logger.info(f"Logged {len(log_data['steps'])} steps with gradient norms.")

    def test_gradient_norms_content_validity(self, temp_output_dir):
        """
        Additional check: Ensure the logged norms are finite and reasonable numbers.
        """
        logs_dir = temp_output_dir / "data" / "logs"
        gradient_log_path = logs_dir / "gradient_norms.json"
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Re-run a minimal training to ensure file exists for this assertion
        train_X, train_y = generate_training_data(n_samples=100, sequence_length=10)
        test_X, test_y = generate_test_data(n_samples=50, sequence_length=10)
        model = create_baseline_transformer(input_dim=train_X.shape[-1], d_model=32, nhead=2, num_layers=1, ff_dim=64)

        config = TrainingConfig(
            epochs=1,
            batch_size=16,
            lr=1e-3,
            device="cpu",
            log_interval=1,
            gradient_clip_value=1.0,
            log_gradient_norms=True,
            gradient_log_path=str(gradient_log_path)
        )

        run_training(
            model=model,
            train_loader=torch.utils.data.DataLoader(
                torch.utils.data.TensorDataset(torch.FloatTensor(train_X), torch.FloatTensor(train_y)),
                batch_size=config.batch_size,
                shuffle=True
            ),
            test_loader=torch.utils.data.DataLoader(
                torch.utils.data.TensorDataset(torch.FloatTensor(test_X), torch.FloatTensor(test_y)),
                batch_size=config.batch_size
            ),
            config=config
        )

        # Load and validate
        log_data = load_gradient_norms(str(gradient_log_path))
        
        for step_entry in log_data["steps"]:
            for param_name, norm_val in step_entry["norms"].items():
                assert isinstance(norm_val, (int, float)), f"Norm value for {param_name} must be numeric."
                assert np.isfinite(norm_val), f"Norm value for {param_name} must be finite."
                assert norm_val >= 0, f"Norm value for {param_name} must be non-negative."

        logger.info("Gradient norms content validation passed.")