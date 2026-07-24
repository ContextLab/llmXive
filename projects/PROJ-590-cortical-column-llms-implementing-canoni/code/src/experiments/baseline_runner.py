"""
Baseline Runner for Cortical Column LLMs Project.

Manages experiment configuration, execution, and logging for the baseline
Transformer model on synthetic datasets (Lorenz, Fourier, Polynomials).

This module orchestrates the training and evaluation pipeline defined in
src/training/trainer.py, ensuring reproducible runs with deterministic seeding
and structured logging of metrics.
"""

import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
from pathlib import Path

import torch
import numpy as np

# Import from project modules (API surface)
from src.models.baseline_transformer import BaselineTransformer
from src.training.trainer import TrainingConfig, run_training, get_resource_usage
from src.data.benchmarks import generate_synthetic_dataset, SyntheticDatasetConfig
from src.training.homeostasis import HomeostasisConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/baseline_runner.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ExperimentConfig:
    """Configuration for a single baseline experiment run."""
    name: str
    dataset_type: str  # 'lorenz', 'fourier', 'polynomial'
    seed: int = 42
    epochs: int = 10
    batch_size: int = 32
    learning_rate: float = 1e-3
    hidden_dim: int = 128
    num_layers: int = 4
    num_heads: int = 4
    dropout: float = 0.1
    max_tokens: int = 512
    train_size: int = 1000
    val_size: int = 200
    test_size: int = 200
    output_dir: str = "data/results"
    log_dir: str = "logs"
    device: str = "cpu"
    gradient_clip_norm: float = 1.0
    use_homeostasis: bool = False
    homeostasis_config: Optional[HomeostasisConfig] = None

    def __post_init__(self):
        """Validate and initialize paths."""
        self.output_path = Path(self.output_dir)
        self.log_path = Path(self.log_dir)
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.log_path.mkdir(parents=True, exist_ok=True)

        # Set deterministic seeds
        torch.manual_seed(self.seed)
        np.random.seed(self.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.seed)


@dataclass
class ExperimentResult:
    """Container for experiment results and metrics."""
    config_name: str
    dataset_type: str
    seed: int
    start_time: float
    end_time: float
    duration_seconds: float
    train_metrics: Dict[str, Any]
    val_metrics: Dict[str, Any]
    test_metrics: Dict[str, Any]
    resource_usage: Dict[str, Any]
    model_path: str
    config_path: str
    success: bool
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def save_json(self, path: Path) -> None:
        """Save result to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


class BaselineRunner:
    """
    Orchestrates baseline Transformer experiments.

    Handles dataset generation, model initialization, training execution,
    and result logging for the baseline control model.
    """

    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.logger = logging.getLogger(f"BaselineRunner.{config.name}")
        self.device = torch.device(config.device)

    def _setup_dataset(self) -> tuple:
        """Generate synthetic datasets based on configuration."""
        self.logger.info(f"Generating {self.config.dataset_type} dataset...")

        # Map dataset type to generator
        if self.config.dataset_type == 'lorenz':
            dataset_config = SyntheticDatasetConfig(
                type='lorenz',
                train_size=self.config.train_size,
                val_size=self.config.val_size,
                test_size=self.config.test_size,
                max_tokens=self.config.max_tokens,
                seed=self.config.seed
            )
        elif self.config.dataset_type == 'fourier':
            dataset_config = SyntheticDatasetConfig(
                type='fourier',
                train_size=self.config.train_size,
                val_size=self.config.val_size,
                test_size=self.config.test_size,
                max_tokens=self.config.max_tokens,
                seed=self.config.seed
            )
        elif self.config.dataset_type == 'polynomial':
            dataset_config = SyntheticDatasetConfig(
                type='polynomial',
                train_size=self.config.train_size,
                val_size=self.config.val_size,
                test_size=self.config.test_size,
                max_tokens=self.config.max_tokens,
                seed=self.config.seed
            )
        else:
            raise ValueError(f"Unknown dataset type: {self.config.dataset_type}")

        try:
            train_data, val_data, test_data = generate_synthetic_dataset(dataset_config)
            self.logger.info(f"Dataset generated: Train={len(train_data)}, Val={len(val_data)}, Test={len(test_data)}")
            return train_data, val_data, test_data
        except Exception as e:
            self.logger.error(f"Failed to generate dataset: {e}")
            raise

    def _setup_model(self) -> BaselineTransformer:
        """Initialize the baseline Transformer model."""
        self.logger.info(f"Initializing BaselineTransformer (hidden={self.config.hidden_dim}, layers={self.config.num_layers})")

        model = BaselineTransformer(
            input_dim=10,  # Assumed input dimension for synthetic data
            hidden_dim=self.config.hidden_dim,
            num_layers=self.config.num_layers,
            num_heads=self.config.num_heads,
            dropout=self.config.dropout,
            device=self.device
        )

        # Move to device
        model = model.to(self.device)
        param_count = sum(p.numel() for p in model.parameters())
        self.logger.info(f"Model initialized with {param_count:,} parameters")

        return model

    def run(self) -> ExperimentResult:
        """
        Execute the full experiment pipeline.

        Returns:
            ExperimentResult: Object containing all metrics and paths.
        """
        start_time = time.time()
        self.logger.info(f"Starting experiment: {self.config.name}")

        try:
            # Setup
            train_data, val_data, test_data = self._setup_dataset()
            model = self._setup_model()

            # Training config
            train_config = TrainingConfig(
                epochs=self.config.epochs,
                batch_size=self.config.batch_size,
                learning_rate=self.config.learning_rate,
                gradient_clip_norm=self.config.gradient_clip_norm,
                device=self.device,
                seed=self.config.seed,
                use_homeostasis=self.config.use_homeostasis,
                homeostasis_config=self.config.config.homeostasis_config if self.config.use_homeostasis else None
            )

            # Run training
            self.logger.info("Starting training loop...")
            train_metrics, val_metrics, test_metrics = run_training(
                model=model,
                train_data=train_data,
                val_data=val_data,
                test_data=test_data,
                config=train_config,
                logger=self.logger
            )

            # Resource usage
            resource_usage = get_resource_usage()

            # Save model
            model_path = self.config.output_path / f"model_{self.config.name}.pt"
            torch.save(model.state_dict(), model_path)

            # Save config
            config_path = self.config.output_path / f"config_{self.config.name}.json"
            with open(config_path, 'w') as f:
                json.dump(asdict(self.config), f, indent=2)

            end_time = time.time()
            duration = end_time - start_time

            result = ExperimentResult(
                config_name=self.config.name,
                dataset_type=self.config.dataset_type,
                seed=self.config.seed,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
                train_metrics=train_metrics,
                val_metrics=val_metrics,
                test_metrics=test_metrics,
                resource_usage=resource_usage,
                model_path=str(model_path),
                config_path=str(config_path),
                success=True
            )

            # Save result
            result_path = self.config.output_path / f"result_{self.config.name}.json"
            result.save_json(result_path)

            self.logger.info(f"Experiment completed successfully in {duration:.2f}s")
            self.logger.info(f"Test MAE: {test_metrics.get('mae', 'N/A'):.4f}")

            return result

        except Exception as e:
            end_time = time.time()
            self.logger.error(f"Experiment failed: {e}", exc_info=True)

            return ExperimentResult(
                config_name=self.config.name,
                dataset_type=self.config.dataset_type,
                seed=self.config.seed,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=end_time - start_time,
                train_metrics={},
                val_metrics={},
                test_metrics={},
                resource_usage={},
                model_path="",
                config_path="",
                success=False,
                error_message=str(e)
            )


def main():
    """Entry point for running baseline experiments."""
    # Default configuration for testing
    config = ExperimentConfig(
        name="baseline_lorenz_test",
        dataset_type="lorenz",
        seed=42,
        epochs=5,
        batch_size=16,
        learning_rate=1e-3,
        hidden_dim=64,
        num_layers=2,
        num_heads=2,
        dropout=0.1,
        max_tokens=128,
        train_size=200,
        val_size=50,
        test_size=50
    )

    runner = BaselineRunner(config)
    result = runner.run()

    if result.success:
        print(f"Experiment '{result.config_name}' completed successfully.")
        print(f"Test MAE: {result.test_metrics.get('mae', 0):.4f}")
        print(f"Duration: {result.duration_seconds:.2f}s")
    else:
        print(f"Experiment '{result.config_name}' failed: {result.error_message}")
        sys.exit(1)


if __name__ == "__main__":
    main()