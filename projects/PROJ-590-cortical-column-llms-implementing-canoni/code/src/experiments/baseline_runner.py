import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

# Import from project API surface
from src.models.baseline_transformer import BaselineTransformer
from src.training.trainer import TrainingConfig, run_training, calculate_mae
from src.data.benchmarks import generate_training_data, generate_test_data

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ExperimentConfig:
    """Configuration for a baseline experiment."""
    hidden_dim: int = 64
    num_layers: int = 4
    num_heads: int = 4
    seq_len: int = 32
    batch_size: int = 32
    epochs: int = 10
    learning_rate: float = 1e-3
    device: str = 'cpu'
    seed: int = 42
    output_path: str = 'data/results/baseline_metrics.json'


@dataclass
class ExperimentResult:
    """Result of a baseline experiment."""
    train_mae: float
    test_mae: float
    degradation_pct: float
    duration_seconds: float
    config: Dict[str, Any] = field(default_factory=dict)


class BaselineRunner:
    """Runner for baseline Transformer experiments on synthetic data."""

    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.device = torch.device(config.device)
        torch.manual_seed(config.seed)

    def _build_model(self) -> BaselineTransformer:
        """Instantiate the baseline Transformer model."""
        model = BaselineTransformer(
            hidden_dim=self.config.hidden_dim,
            num_layers=self.config.num_layers,
            num_heads=self.config.num_heads,
            seq_len=self.config.seq_len
        )
        return model.to(self.device)

    def _prepare_data(self):
        """Generate and prepare training and test datasets."""
        logger.info("Generating synthetic training data (Lorenz attractor)...")
        train_X, train_y = generate_training_data(
            num_samples=1000,
            seq_len=self.config.seq_len,
            noise_level=0.01,
            seed=self.config.seed
        )

        logger.info("Generating synthetic test data (Polynomials/Fourier)...")
        test_X, test_y = generate_test_data(
            num_samples=500,
            seq_len=self.config.seq_len,
            noise_level=0.01,
            seed=self.config.seed + 1  # Different seed for independence
        )

        # Convert to tensors
        train_X = torch.tensor(train_X, dtype=torch.float32)
        train_y = torch.tensor(train_y, dtype=torch.float32)
        test_X = torch.tensor(test_X, dtype=torch.float32)
        test_y = torch.tensor(test_y, dtype=torch.float32)

        # Create DataLoaders
        train_dataset = TensorDataset(train_X, train_y)
        test_dataset = TensorDataset(test_X, test_y)

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

        return train_loader, test_loader

    def run_and_record_metrics(self) -> ExperimentResult:
        """
        Run the baseline model on training and test sets, calculate metrics,
        and store results in data/results/baseline_metrics.json.

        Returns:
            ExperimentResult containing train_mae, test_mae, and degradation_pct.
        """
        logger.info("Starting baseline experiment run...")
        start_time = time.time()

        # Prepare data
        train_loader, test_loader = self._prepare_data()

        # Build model
        model = self._build_model()
        optimizer = optim.Adam(model.parameters(), lr=self.config.learning_rate)
        criterion = nn.MSELoss()

        # Training configuration
        training_config = TrainingConfig(
            epochs=self.config.epochs,
            batch_size=self.config.batch_size,
            learning_rate=self.config.learning_rate,
            device=self.config.device,
            seed=self.config.seed,
            gradient_clip_norm=1.0,
            log_gradient_norms=False  # We handle logging separately if needed
        )

        # Train the model
        logger.info(f"Training for {self.config.epochs} epochs...")
        train_metrics = run_training(
            model=model,
            train_loader=train_loader,
            optimizer=optimizer,
            criterion=criterion,
            config=training_config
        )

        # Evaluate on training set
        model.eval()
        train_mae = calculate_mae(model, train_loader, criterion, self.device)
        logger.info(f"Train MAE: {train_mae:.6f}")

        # Evaluate on test set
        test_mae = calculate_mae(model, test_loader, criterion, self.device)
        logger.info(f"Test MAE: {test_mae:.6f}")

        # Calculate degradation percentage
        if train_mae > 0:
            degradation_pct = ((test_mae - train_mae) / train_mae) * 100
        else:
            degradation_pct = 0.0

        duration_seconds = time.time() - start_time

        result = ExperimentResult(
            train_mae=float(train_mae),
            test_mae=float(test_mae),
            degradation_pct=float(degradation_pct),
            duration_seconds=duration_seconds,
            config=asdict(self.config)
        )

        # Write results to JSON file
        output_path = self.config.output_path
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        result_dict = {
            'train_mae': result.train_mae,
            'test_mae': result.test_mae,
            'degradation_pct': result.degradation_pct,
            'duration_seconds': result.duration_seconds,
            'config': result.config
        }

        with open(output_path, 'w') as f:
            json.dump(result_dict, f, indent=2)

        logger.info(f"Results written to {output_path}")
        logger.info(f"Experiment completed in {duration_seconds:.2f} seconds")

        return result


def main():
    """Entry point for running the baseline experiment."""
    config = ExperimentConfig(
        hidden_dim=64,
        num_layers=4,
        num_heads=4,
        seq_len=32,
        batch_size=32,
        epochs=10,
        learning_rate=1e-3,
        device='cpu',
        seed=42,
        output_path='data/results/baseline_metrics.json'
    )

    runner = BaselineRunner(config)
    result = runner.run_and_record_metrics()

    print(f"\n=== Baseline Experiment Results ===")
    print(f"Train MAE: {result.train_mae:.6f}")
    print(f"Test MAE: {result.test_mae:.6f}")
    print(f"Degradation: {result.degradation_pct:.2f}%")
    print(f"Duration: {result.duration_seconds:.2f}s")


if __name__ == '__main__':
    main()
