"""
Baseline Runner for Cortical Column LLMs Project.

This module manages experiment configuration, logging, and execution
for the baseline Transformer model on synthetic tasks.
"""

import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, Optional, List

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

# Import from project modules
from src.models.baseline_transformer import BaselineTransformer
from src.data.benchmarks import generate_training_data, generate_test_data
from src.training.trainer import run_training, TrainingConfig, TrainingMetrics
from src.training.homeostasis import log_gradient_norms

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/logs/baseline_runner.log')
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ExperimentConfig:
    """Configuration for a baseline experiment."""
    name: str = "baseline_experiment"
    hidden_dim: int = 64
    num_layers: int = 4
    num_heads: int = 4
    dropout: float = 0.1
    learning_rate: float = 1e-4
    batch_size: int = 32
    num_epochs: int = 10
    seed: int = 42
    log_gradients: bool = True
    gradient_log_path: str = "data/logs/gradient_norms.json"
    metrics_output_path: str = "data/results/baseline_metrics.json"

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExperimentConfig':
        """Create config from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ExperimentResult:
    """Results from a baseline experiment."""
    name: str
    train_mae: float
    test_mae: float
    degradation_pct: float
    training_time: float
    config: Dict[str, Any]
    metrics: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return asdict(self)


class BaselineRunner:
    """Manages baseline Transformer experiment execution and logging."""

    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.device = torch.device('cpu')  # CPU-optimized as per project constraints
        self.model: Optional[BaselineTransformer] = None
        self.training_metrics: Optional[TrainingMetrics] = None
        self.result: Optional[ExperimentResult] = None

        # Ensure output directories exist
        Path(self.config.gradient_log_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.config.metrics_output_path).parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized BaselineRunner with config: {self.config.name}")

    def _set_seed(self):
        """Set random seeds for reproducibility."""
        torch.manual_seed(self.config.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(self.config.seed)
        logger.info(f"Random seed set to {self.config.seed}")

    def _build_model(self) -> BaselineTransformer:
        """Build the baseline Transformer model."""
        model = BaselineTransformer(
            hidden_dim=self.config.hidden_dim,
            num_layers=self.config.num_layers,
            num_heads=self.config.num_heads,
            dropout=self.config.dropout
        )
        model = model.to(self.device)
        logger.info(f"Built model with {sum(p.numel() for p in model.parameters()):,} parameters")
        return model

    def _prepare_data(self) -> tuple:
        """Prepare training and test datasets from synthetic benchmarks."""
        logger.info("Generating training data (Lorenz attractor)...")
        train_X, train_y = generate_training_data(seed=self.config.seed)

        logger.info("Generating test data (Polynomials/Fourier)...")
        test_X, test_y = generate_test_data(seed=self.config.seed + 1)  # Different seed for independence

        # Convert to tensors
        train_dataset = TensorDataset(
            torch.FloatTensor(train_X),
            torch.FloatTensor(train_y)
        )
        test_dataset = TensorDataset(
            torch.FloatTensor(test_X),
            torch.FloatTensor(test_y)
        )

        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True
        )
        test_loader = DataLoader(
            test_dataset,
            batch_size=self.config.batch_size,
            shuffle=False
        )

        logger.info(f"Training set: {len(train_X)} samples, Test set: {len(test_X)} samples")
        return train_loader, test_loader

    def run_experiment(self) -> ExperimentResult:
        """Execute the full baseline experiment."""
        start_time = time.time()

        # Set seeds
        self._set_seed()

        # Build model
        self.model = self._build_model()

        # Prepare data
        train_loader, test_loader = self._prepare_data()

        # Configure training
        training_config = TrainingConfig(
            learning_rate=self.config.learning_rate,
            batch_size=self.config.batch_size,
            num_epochs=self.config.num_epochs,
            seed=self.config.seed,
            gradient_clipping=True,
            max_grad_norm=1.0
        )

        # Run training
        logger.info("Starting training loop...")
        self.training_metrics = run_training(
            model=self.model,
            train_loader=train_loader,
            test_loader=test_loader,
            config=training_config,
            device=self.device
        )

        # Log gradients if enabled
        if self.config.log_gradients and self.model is not None:
            logger.info(f"Logging gradients to {self.config.gradient_log_path}")
            log_gradient_norms(self.model, step=self.config.num_epochs, output_path=self.config.gradient_log_path)

        # Calculate metrics
        train_mae = self.training_metrics.train_mae
        test_mae = self.training_metrics.test_mae

        # Calculate degradation percentage with zero-division handling
        if train_mae > 0:
            degradation_pct = ((test_mae - train_mae) / train_mae) * 100
        else:
            degradation_pct = 0.0

        training_time = time.time() - start_time

        # Create result object
        self.result = ExperimentResult(
            name=self.config.name,
            train_mae=float(train_mae),
            test_mae=float(test_mae),
            degradation_pct=float(degradation_pct),
            training_time=float(training_time),
            config=self.config.to_dict(),
            metrics=self.training_metrics.to_dict() if self.training_metrics else None
        )

        # Save results to JSON
        self._save_results()

        logger.info(f"Experiment completed in {training_time:.2f}s")
        logger.info(f"Train MAE: {train_mae:.6f}, Test MAE: {test_mae:.6f}, Degradation: {degradation_pct:.2f}%")

        return self.result

    def _save_results(self):
        """Save experiment results to JSON file."""
        if self.result is None:
            raise RuntimeError("Cannot save results: experiment not run yet")

        output_path = self.config.metrics_output_path
        with open(output_path, 'w') as f:
            json.dump(self.result.to_dict(), f, indent=2)

        logger.info(f"Results saved to {output_path}")

    def get_result(self) -> Optional[ExperimentResult]:
        """Get the experiment result."""
        return self.result


def main():
    """Main entry point for baseline runner."""
    logger.info("Starting Baseline Runner...")

    # Create default configuration
    config = ExperimentConfig(
        name="baseline_lorenz_polynomial",
        hidden_dim=64,
        num_layers=4,
        num_heads=4,
        dropout=0.1,
        learning_rate=1e-4,
        batch_size=32,
        num_epochs=10,
        seed=42,
        log_gradients=True,
        gradient_log_path="data/logs/gradient_norms.json",
        metrics_output_path="data/results/baseline_metrics.json"
    )

    # Run experiment
    runner = BaselineRunner(config)
    result = runner.run_experiment()

    logger.info("Baseline Runner completed successfully")
    return result


if __name__ == "__main__":
    main()