"""
Baseline Runner for Cortical Column LLMs Project.

This module manages experiment configuration and logging for the baseline
Transformer training pipeline (User Story 1). It orchestrates the training
process, handles configuration loading/saving, and ensures all metrics
are properly logged to the designated output files.
"""

import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
import torch
import numpy as np

# Import core training components
from src.training.trainer import TrainingConfig, run_training, calculate_mae
from src.models.baseline_transformer import BaselineTransformer, create_baseline_transformer
from src.data.benchmarks import generate_synthetic_dataset, SyntheticTaskType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ExperimentConfig:
    """Configuration for a baseline experiment run."""
    task_type: SyntheticTaskType = SyntheticTaskType.LORENZ
    model_name: str = "baseline_transformer"
    hidden_dim: int = 64
    num_layers: int = 4
    num_heads: int = 4
    seq_len: int = 128
    batch_size: int = 32
    epochs: int = 10
    learning_rate: float = 1e-3
    weight_decay: float = 1e-4
    seed: int = 42
    device: str = "cpu"
    output_dir: str = "data/results"
    log_dir: str = "data/logs"
    gradient_logging: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for JSON serialization."""
        return {
            "task_type": self.task_type.value,
            "model_name": self.model_name,
            "hidden_dim": self.hidden_dim,
            "num_layers": self.num_layers,
            "num_heads": self.num_heads,
            "seq_len": self.seq_len,
            "batch_size": self.batch_size,
            "epochs": self.epochs,
            "learning_rate": self.learning_rate,
            "weight_decay": self.weight_decay,
            "seed": self.seed,
            "device": self.device,
            "output_dir": self.output_dir,
            "log_dir": self.log_dir,
            "gradient_logging": self.gradient_logging
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExperimentConfig':
        """Create config from dictionary."""
        # Handle task_type conversion
        if "task_type" in data and isinstance(data["task_type"], str):
            data["task_type"] = SyntheticTaskType(data["task_type"])
        return cls(**data)


@dataclass
class ExperimentResult:
    """Result of a baseline experiment run."""
    task_type: str
    config: Dict[str, Any]
    train_mae: float
    test_mae: float
    degradation_pct: float
    total_time_seconds: float
    peak_memory_mb: float
    gradient_norms_logged: bool
    seed: int
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return asdict(self)


class BaselineRunner:
    """
    Manages baseline experiment configuration, execution, and logging.

    This class orchestrates the training of the baseline Transformer model
    on synthetic datasets, handles configuration management, and ensures
    all metrics are properly logged.
    """

    def __init__(self, config: Optional[ExperimentConfig] = None):
        """
        Initialize the BaselineRunner.

        Args:
            config: ExperimentConfig instance. If None, uses default config.
        """
        self.config = config or ExperimentConfig()
        self.logger = logger
        self._setup_directories()

    def _setup_directories(self) -> None:
        """Ensure all required directories exist."""
        os.makedirs(self.config.output_dir, exist_ok=True)
        os.makedirs(self.config.log_dir, exist_ok=True)

    def _save_config(self) -> str:
        """Save experiment configuration to file."""
        config_path = os.path.join(
            self.config.output_dir,
            f"baseline_config_{self.config.task_type.value}.json"
        )
        with open(config_path, 'w') as f:
            json.dump(self.config.to_dict(), f, indent=2)
        self.logger.info(f"Saved experiment config to {config_path}")
        return config_path

    def _generate_datasets(self) -> tuple:
        """Generate train and test datasets for the specified task."""
        self.logger.info(f"Generating synthetic dataset for task: {self.config.task_type.value}")

        # Generate training data
        train_X, train_y = generate_synthetic_dataset(
            task_type=self.config.task_type,
            num_samples=1000,
            seq_len=self.config.seq_len,
            seed=self.config.seed
        )

        # Generate test data
        test_X, test_y = generate_synthetic_dataset(
            task_type=self.config.task_type,
            num_samples=200,
            seq_len=self.config.seq_len,
            seed=self.config.seed + 1000  # Different seed for test
        )

        self.logger.info(f"Generated {len(train_X)} train samples and {len(test_X)} test samples")
        return train_X, train_y, test_X, test_y

    def _create_model(self) -> BaselineTransformer:
        """Create and initialize the baseline model."""
        self.logger.info("Creating baseline Transformer model")

        model = create_baseline_transformer(
            hidden_dim=self.config.hidden_dim,
            num_layers=self.config.num_layers,
            num_heads=self.config.num_heads,
            seq_len=self.config.seq_len,
            device=self.config.device
        )

        param_count = sum(p.numel() for p in model.parameters())
        self.logger.info(f"Model created with {param_count:,} parameters")

        return model

    def run_experiment(self) -> ExperimentResult:
        """
        Execute the baseline experiment.

        Returns:
            ExperimentResult containing all metrics and metadata.
        """
        start_time = time.time()
        self.logger.info("Starting baseline experiment")

        # Save configuration
        config_path = self._save_config()

        # Generate datasets
        train_X, train_y, test_X, test_y = self._generate_datasets()

        # Create model
        model = self._create_model()

        # Prepare training config
        training_config = TrainingConfig(
            epochs=self.config.epochs,
            batch_size=self.config.batch_size,
            learning_rate=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
            device=self.config.device,
            seed=self.config.seed,
            gradient_logging=self.config.gradient_logging,
            log_dir=self.config.log_dir
        )

        # Run training
        self.logger.info(f"Starting training for {self.config.epochs} epochs")
        train_metrics, model_state = run_training(
            model=model,
            train_X=train_X,
            train_y=train_y,
            test_X=test_X,
            test_y=test_y,
            config=training_config
        )

        # Calculate final metrics
        end_time = time.time()
        total_time = end_time - start_time

        # Calculate MAE on train and test sets
        train_mae = calculate_mae(train_y, train_metrics['train_predictions'])
        test_mae = calculate_mae(test_y, train_metrics['test_predictions'])

        # Calculate degradation
        degradation_pct = ((test_mae - train_mae) / train_mae) * 100 if train_mae > 0 else 0.0

        # Get memory usage
        import psutil
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / (1024 * 1024)

        # Prepare result
        result = ExperimentResult(
            task_type=self.config.task_type.value,
            config=self.config.to_dict(),
            train_mae=float(train_mae),
            test_mae=float(test_mae),
            degradation_pct=float(degradation_pct),
            total_time_seconds=float(total_time),
            peak_memory_mb=float(memory_mb),
            gradient_norms_logged=self.config.gradient_logging,
            seed=self.config.seed,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )

        # Save results
        self._save_results(result)

        self.logger.info(f"Experiment completed in {total_time:.2f}s")
        self.logger.info(f"Train MAE: {train_mae:.4f}, Test MAE: {test_mae:.4f}")
        self.logger.info(f"Degradation: {degradation_pct:.2f}%")

        return result

    def _save_results(self, result: ExperimentResult) -> None:
        """Save experiment results to file."""
        results_path = os.path.join(
            self.config.output_dir,
            f"baseline_results_{self.config.task_type.value}.json"
        )

        with open(results_path, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)

        self.logger.info(f"Saved results to {results_path}")

    def run_multiple_tasks(self, task_types: List[SyntheticTaskType]) -> List[ExperimentResult]:
        """
        Run experiments on multiple task types.

        Args:
            task_types: List of task types to run.

        Returns:
            List of ExperimentResult instances.
        """
        results = []
        for task_type in task_types:
          self.logger.info(f"Running experiment for task: {task_type.value}")
          self.config.task_type = task_type
          result = self.run_experiment()
          results.append(result)
        return results


def main():
    """Main entry point for baseline runner."""
    parser = argparse.ArgumentParser(description="Run baseline Transformer experiments")
    parser.add_argument(
        "--task",
        type=str,
        choices=["lorenz", "fourier", "polynomial"],
        default="lorenz",
        help="Task type to run"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=10,
        help="Number of training epochs"
    )
    parser.add_argument(
        "--hidden-dim",
        type=int,
        default=64,
        help="Model hidden dimension"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/results",
        help="Output directory for results"
    )

    args = parser.parse_args()

    # Map string to task type
    task_map = {
        "lorenz": SyntheticTaskType.LORENZ,
        "fourier": SyntheticTaskType.FOURIER,
        "polynomial": SyntheticTaskType.POLYNOMIAL
    }

    config = ExperimentConfig(
        task_type=task_map[args.task],
        epochs=args.epochs,
        hidden_dim=args.hidden_dim,
        output_dir=args.output_dir
    )

    runner = BaselineRunner(config)
    result = runner.run_experiment()

    print(f"\nExperiment completed:")
    print(f"  Task: {result.task_type}")
    print(f"  Train MAE: {result.train_mae:.4f}")
    print(f"  Test MAE: {result.test_mae:.4f}")
    print(f"  Degradation: {result.degradation_pct:.2f}%")
    print(f"  Time: {result.total_time_seconds:.2f}s")
    print(f"  Results saved to: {args.output_dir}")


if __name__ == "__main__":
    import argparse
    main()