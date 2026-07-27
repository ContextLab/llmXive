"""
Baseline Runner for Cortical Column LLM Experiments.

Manages experiment configuration, execution, and logging for the baseline
Transformer model on synthetic tasks (Lorenz, Fourier, Polynomials).
"""
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
from pathlib import Path

import torch
import torch.nn as nn
import numpy as np

# Import from project modules based on API surface
from src.models.baseline_transformer import create_baseline_transformer
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
    """Configuration for a single baseline experiment run."""
    name: str
    seed: int
    task_type: str  # 'lorenz', 'fourier', 'polynomial'
    hidden_dim: int = 64
    num_layers: int = 4
    num_heads: int = 4
    seq_len: int = 128
    batch_size: int = 32
    epochs: int = 10
    lr: float = 1e-3
    weight_decay: float = 1e-4
    gradient_clip: float = 1.0
    log_gradient_norms: bool = True
    output_dir: str = "data/results"
    state_dir: str = "state"

    def __post_init__(self):
        # Ensure output directories exist
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.state_dir).mkdir(parents=True, exist_ok=True)


@dataclass
class ExperimentResult:
    """Result of a single experiment run."""
    config_name: str
    seed: int
    task_type: str
    train_mae: float
    test_mae: float
    degradation_pct: float
    total_time_seconds: float
    peak_memory_mb: float
    gradient_norm_stats: Optional[Dict[str, float]] = None
    model_path: Optional[str] = None
    config_path: Optional[str] = None
    metrics_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class BaselineRunner:
    """
    Orchestrates baseline Transformer training and evaluation.

    Handles configuration, data generation, model training, and result logging.
    """

    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.logger = logger
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.logger.info(f"Using device: {self.device}")

    def _generate_data(self) -> tuple:
        """Generate training and test data based on task type."""
        self.logger.info(f"Generating data for task: {self.config.task_type}")
        torch.manual_seed(self.config.seed)
        np.random.seed(self.config.seed)

        if self.config.task_type == 'lorenz':
            train_data, train_targets = generate_training_data(
                task='lorenz',
                num_samples=1000,
                seq_len=self.config.seq_len,
                seed=self.config.seed
            )
            test_data, test_targets = generate_test_data(
                task='polynomial',  # Independent distribution as per T005
                num_samples=200,
                seq_len=self.config.seq_len,
                seed=self.config.seed + 1000
            )
        elif self.config.task_type == 'fourier':
            train_data, train_targets = generate_training_data(
                task='fourier',
                num_samples=1000,
                seq_len=self.config.seq_len,
                seed=self.config.seed
            )
            test_data, test_targets = generate_test_data(
                task='lorenz',
                num_samples=200,
                seq_len=self.config.seq_len,
                seed=self.config.seed + 1000
            )
        else:  # polynomial
            train_data, train_targets = generate_training_data(
                task='polynomial',
                num_samples=1000,
                seq_len=self.config.seq_len,
                seed=self.config.seed
            )
            test_data, test_targets = generate_test_data(
                task='fourier',
                num_samples=200,
                seq_len=self.config.seq_len,
                seed=self.config.seed + 1000
            )

        self.logger.info(f"Training data shape: {train_data.shape}")
        self.logger.info(f"Test data shape: {test_data.shape}")

        return train_data, train_targets, test_data, test_targets

    def _create_model(self) -> nn.Module:
        """Create the baseline Transformer model."""
        self.logger.info(
            f"Creating model: hidden_dim={self.config.hidden_dim}, "
            f"layers={self.config.num_layers}, heads={self.config.num_heads}"
        )
        model = create_baseline_transformer(
            input_dim=train_data.shape[-1] if 'train_data' in locals() else 10,
            hidden_dim=self.config.hidden_dim,
            num_layers=self.config.num_layers,
            num_heads=self.config.num_heads,
            seq_len=self.config.seq_len
        )
        model = model.to(self.device)
        return model

    def run(self) -> ExperimentResult:
        """Execute the full experiment pipeline."""
        start_time = time.time()
        self.logger.info(f"Starting experiment: {self.config.name}")

        # Generate data
        train_data, train_targets, test_data, test_targets = self._generate_data()

        # Create model
        model = self._create_model()

        # Setup training config
        training_config = TrainingConfig(
            epochs=self.config.epochs,
            batch_size=self.config.batch_size,
            lr=self.config.lr,
            weight_decay=self.config.weight_decay,
            gradient_clip=self.config.gradient_clip,
            device=str(self.device),
            log_gradient_norms=self.config.log_gradient_norms,
            log_path=os.path.join(self.config.output_dir, "gradient_norms.json")
        )

        # Run training
        self.logger.info("Starting training loop...")
        metrics = run_training(
            model=model,
            train_data=train_data,
            train_targets=train_targets,
            test_data=test_data,
            test_targets=test_targets,
            config=training_config
        )

        # Calculate degradation
        train_mae = metrics['train_mae']
        test_mae = metrics['test_mae']
        if train_mae > 0:
            degradation_pct = (test_mae - train_mae) / train_mae * 100
        else:
            degradation_pct = 0.0

        end_time = time.time()
        total_time = end_time - start_time

        # Save model and metrics
        model_path = os.path.join(self.config.output_dir, f"{self.config.name}_model.pt")
        torch.save(model.state_dict(), model_path)

        config_path = os.path.join(self.config.output_dir, f"{self.config.name}_config.json")
        with open(config_path, 'w') as f:
            json.dump(self.config.to_dict(), f, indent=2)

        metrics_path = os.path.join(self.config.output_dir, f"{self.config.name}_metrics.json")
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)

        # Collect gradient stats if available
        gradient_stats = None
        if self.config.log_gradient_norms:
            gradient_log_path = os.path.join(self.config.output_dir, "gradient_norms.json")
            if os.path.exists(gradient_log_path):
                with open(gradient_log_path, 'r') as f:
                    gradient_data = json.load(f)
                    gradient_stats = {
                        'mean': np.mean(gradient_data.get('norms', [0])),
                        'std': np.std(gradient_data.get('norms', [0])),
                        'max': np.max(gradient_data.get('norms', [0]))
                    }

        result = ExperimentResult(
            config_name=self.config.name,
            seed=self.config.seed,
            task_type=self.config.task_type,
            train_mae=train_mae,
            test_mae=test_mae,
            degradation_pct=degradation_pct,
            total_time_seconds=total_time,
            peak_memory_mb=metrics.get('peak_memory_mb', 0.0),
            gradient_norm_stats=gradient_stats,
            model_path=model_path,
            config_path=config_path,
            metrics_path=metrics_path
        )

        self.logger.info(
            f"Experiment {self.config.name} completed. "
            f"Train MAE: {train_mae:.4f}, Test MAE: {test_mae:.4f}, "
            f"Degradation: {degradation_pct:.2f}%"
        )

        return result


def main():
    """Main entry point for baseline runner."""
    parser = argparse.ArgumentParser(description="Run baseline Transformer experiment")
    parser.add_argument('--name', type=str, default='baseline_lorenz', help='Experiment name')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--task', type=str, default='lorenz', choices=['lorenz', 'fourier', 'polynomial'])
    parser.add_argument('--hidden-dim', type=int, default=64)
    parser.add_argument('--num-layers', type=int, default=4)
    parser.add_argument('--num-heads', type=int, default=4)
    parser.add_argument('--epochs', type=int, default=10)
    parser.add_argument('--lr', type=float, default=1e-3)
    parser.add_argument('--output-dir', type=str, default='data/results')

    args = parser.parse_args()

    config = ExperimentConfig(
        name=args.name,
        seed=args.seed,
        task_type=args.task,
        hidden_dim=args.hidden_dim,
        num_layers=args.num_layers,
        num_heads=args.num_heads,
        epochs=args.epochs,
        lr=args.lr,
        output_dir=args.output_dir
    )

    runner = BaselineRunner(config)
    result = runner.run()

    # Save result summary
    result_path = os.path.join(config.output_dir, f"{config.name}_result.json")
    with open(result_path, 'w') as f:
        json.dump(result.to_dict(), f, indent=2)

    print(f"Results saved to {result_path}")
    return result


if __name__ == '__main__':
    import argparse
    main()