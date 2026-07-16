"""
Baseline Runner for Cortical Column LLMs Project.

Manages experiment configuration, logging, and orchestration for the baseline
Transformer training runs as specified in User Story 1 (US1).
"""

import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch
import psutil

# Import from existing project modules as per API surface
from src.training.trainer import run_training, TrainingConfig, TrainingMetrics
from src.data.benchmarks import generate_synthetic_dataset, SyntheticTaskType


@dataclass
class ExperimentConfig:
    """Configuration for a single baseline experiment run."""
    experiment_id: str
    task_type: SyntheticTaskType
    seed: int = 42
    max_epochs: int = 10
    batch_size: int = 32
    learning_rate: float = 1e-4
    hidden_dim: int = 128
    num_layers: int = 3
    num_heads: int = 4
    dropout: float = 0.1
    output_dir: str = "data/results"
    log_level: str = "INFO"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExperimentResult:
    """Stores the outcome of a baseline experiment run."""
    experiment_id: str
    task_type: str
    seed: int
    start_time: str
    end_time: str
    duration_seconds: float
    metrics: Dict[str, float]
    resource_usage: Dict[str, float]
    config_snapshot: Dict[str, Any]
    status: str  # 'success', 'failed', 'timeout'
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BaselineRunner:
    """
    Orchestrates baseline Transformer experiments.

    Handles:
    - Configuration management
    - Logging setup (file and console)
    - Dataset generation
    - Training execution
    - Result aggregation and storage
    """

    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.experiment_id = config.experiment_id
        self.output_dir = Path(config.output_dir)
        self.results_file = self.output_dir / f"baseline_{self.experiment_id}.json"
        self.log_file = self.output_dir / f"baseline_{self.experiment_id}.log"

        # Ensure output directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self._setup_logging()

        self.logger = logging.getLogger(f"BaselineRunner.{self.experiment_id}")

    def _setup_logging(self) -> None:
        """Configure logging for the experiment."""
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)

        # Clear existing handlers to avoid duplicates in repeated runs
        logger = logging.getLogger(f"BaselineRunner.{self.experiment_id}")
        logger.handlers.clear()
        logger.setLevel(log_level)

        # File handler
        fh = logging.FileHandler(self.log_file)
        fh.setLevel(log_level)
        fh.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(fh)

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(log_level)
        ch.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        logger.addHandler(ch)

    def _get_resource_usage(self) -> Dict[str, float]:
        """Capture current system resource usage."""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()

        return {
            "rss_mb": memory_info.rss / (1024 * 1024),
            "vms_mb": memory_info.vms / (1024 * 1024),
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "num_threads": process.num_threads()
        }

    def _generate_dataset(self, split: str) -> Dict[str, torch.Tensor]:
        """
        Generate synthetic dataset for the configured task type.

        Args:
            split: One of 'train', 'val', 'test'

        Returns:
            Dictionary with 'inputs' and 'targets' tensors.
        """
        self.logger.info(f"Generating {split} dataset for task: {self.config.task_type}")

        # Determine dataset size based on split
        if split == 'train':
            n_samples = 5000
        elif split == 'val':
            n_samples = 1000
        else:
            n_samples = 1000

        # Generate with deterministic seeding
        dataset = generate_synthetic_dataset(
            task_type=self.config.task_type,
            n_samples=n_samples,
            seed=self.config.seed + (1000 if split == 'val' else 2000 if split == 'test' else 0)
        )

        return dataset

    def run(self) -> ExperimentResult:
        """
        Execute the full experiment pipeline.

        Returns:
            ExperimentResult containing metrics and status.
        """
        start_time_str = datetime.now().isoformat()
        start_time = time.time()

        self.logger.info(f"Starting experiment: {self.experiment_id}")
        self.logger.info(f"Configuration: {json.dumps(self.config.to_dict(), indent=2)}")

        try:
            # Generate datasets
            train_data = self._generate_dataset('train')
            val_data = self._generate_dataset('val')
            test_data = self._generate_dataset('test')

            self.logger.info(f"Dataset sizes - Train: {len(train_data['inputs'])}, "
                             f"Val: {len(val_data['inputs'])}, Test: {len(test_data['inputs'])}")

            # Setup training configuration
            training_config = TrainingConfig(
                seed=self.config.seed,
                max_epochs=self.config.max_epochs,
                batch_size=self.config.batch_size,
                learning_rate=self.config.learning_rate,
                hidden_dim=self.config.hidden_dim,
                num_layers=self.config.num_layers,
                num_heads=self.config.num_heads,
                dropout=self.config.dropout,
                device='cpu',  # Enforce CPU as per project constraints
                log_interval=10
            )

            # Run training
            self.logger.info("Starting training loop...")
            metrics = run_training(
                model_type='baseline_transformer',
                train_data=train_data,
                val_data=val_data,
                test_data=test_data,
                config=training_config
            )

            # Capture final resource usage
            resource_usage = self._get_resource_usage()

            end_time = time.time()
            end_time_str = datetime.now().isoformat()

            result = ExperimentResult(
                experiment_id=self.experiment_id,
                task_type=self.config.task_type,
                seed=self.config.seed,
                start_time=start_time_str,
                end_time=end_time_str,
                duration_seconds=end_time - start_time,
                metrics=metrics,
                resource_usage=resource_usage,
                config_snapshot=self.config.to_dict(),
                status='success'
            )

            self.logger.info(f"Experiment completed successfully. "
                             f"Duration: {result.duration_seconds:.2f}s, "
                             f"Test MAE: {metrics.get('test_mae', 'N/A')}")

            # Save results
            self._save_result(result)

            return result

        except Exception as e:
            end_time = time.time()
            self.logger.error(f"Experiment failed with error: {str(e)}", exc_info=True)

            return ExperimentResult(
                experiment_id=self.experiment_id,
                task_type=self.config.task_type,
                seed=self.config.seed,
                start_time=start_time_str,
                end_time=datetime.now().isoformat(),
                duration_seconds=end_time - start_time,
                metrics={},
                resource_usage=self._get_resource_usage(),
                config_snapshot=self.config.to_dict(),
                status='failed',
                error_message=str(e)
            )

    def _save_result(self, result: ExperimentResult) -> None:
        """Save experiment result to JSON file."""
        result_dict = result.to_dict()

        with open(self.results_file, 'w') as f:
            json.dump(result_dict, f, indent=2, default=str)

        self.logger.info(f"Results saved to: {self.results_file}")


def main():
    """Entry point for running a baseline experiment."""
    # Default configuration for a standard run
    config = ExperimentConfig(
        experiment_id="lorenz_baseline_001",
        task_type="lorenz_attractor",
        seed=42,
        max_epochs=15,
        batch_size=32,
        learning_rate=1e-3,
        hidden_dim=256,
        num_layers=4,
        num_heads=8,
        dropout=0.1,
        output_dir="data/results",
        log_level="INFO"
    )

    runner = BaselineRunner(config)
    result = runner.run()

    # Exit with non-zero code if experiment failed
    if result.status == 'failed':
        sys.exit(1)


if __name__ == "__main__":
    main()