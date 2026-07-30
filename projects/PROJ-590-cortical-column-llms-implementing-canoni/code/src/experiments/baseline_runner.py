import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field, asdict

import torch
import numpy as np

# Import existing project APIs
from src.data.benchmarks import generate_training_data, generate_test_data
from src.models.baseline_transformer import BaselineTransformer
from src.training.trainer import TrainingConfig, run_training, calculate_mae
from src.utils.statistics import load_gradient_norms

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ExperimentConfig:
    """Configuration for a baseline experiment."""
    name: str = "baseline_experiment"
    seed: int = 42
    hidden_dim: int = 64
    num_heads: int = 4
    num_layers: int = 2
    batch_size: int = 32
    epochs: int = 10
    learning_rate: float = 1e-3
    lr_scheduler: str = "step"
    lr_step_size: int = 5
    lr_gamma: float = 0.5
    weight_decay: float = 1e-4
    max_grad_norm: float = 1.0
    device: str = "cpu"
    log_gradient_norms: bool = True
    output_dir: str = "data/results"
    log_dir: str = "data/logs"


@dataclass
class ExperimentResult:
    """Result of a baseline experiment."""
    config_name: str
    train_mae: float
    test_mae: float
    degradation_pct: float
    total_time_seconds: float
    epoch_count: int
    device: str
    seed: int
    params_count: int


class BaselineRunner:
    """Manages baseline transformer training and metric recording."""

    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.output_dir = config.output_dir
        self.log_dir = config.log_dir
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)

    def run_and_record_metrics(self) -> ExperimentResult:
        """
        Run baseline on training set (Lorenz) and test set (Polynomials).
        Calculate train_mae, test_mae, and degradation_pct.
        Store results in data/results/baseline_metrics.json.

        Logic:
        1. Generate training data (Lorenz) and test data (Polynomials).
        2. Initialize BaselineTransformer.
        3. Train using run_training.
        4. Evaluate on train and test sets.
        5. Calculate degradation_pct.
        6. Log warning if degradation >= 10% (do not raise).
        7. Save JSON artifact.
        """
        logger.info(f"Starting baseline experiment: {self.config.name}")
        start_time = time.time()

        # Set seed for reproducibility
        torch.manual_seed(self.config.seed)
        np.random.seed(self.config.seed)

        # 1. Generate Data
        # T005a: generate_training_data -> Lorenz
        # T005a: generate_test_data -> Polynomials/Fourier
        logger.info("Generating training data (Lorenz)...")
        train_data = generate_training_data(seed=self.config.seed)
        logger.info(f"Training data shape: {train_data['X'].shape}")

        logger.info("Generating test data (Polynomials)...")
        test_data = generate_test_data(seed=self.config.seed)
        logger.info(f"Test data shape: {test_data['X'].shape}")

        # 2. Initialize Model
        logger.info("Initializing BaselineTransformer...")
        model = BaselineTransformer(
            hidden_dim=self.config.hidden_dim,
            num_heads=self.config.num_heads,
            num_layers=self.config.num_layers,
            input_dim=train_data['X'].shape[-1],
            output_dim=train_data['y'].shape[-1]
        )
        model.to(self.config.device)
        params_count = sum(p.numel() for p in model.parameters())
        logger.info(f"Model parameters: {params_count}")

        # 3. Configure Training
        training_config = TrainingConfig(
            epochs=self.config.epochs,
            batch_size=self.config.batch_size,
            learning_rate=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
            max_grad_norm=self.config.max_grad_norm,
            lr_scheduler=self.config.lr_scheduler,
            lr_step_size=self.config.lr_step_size,
            lr_gamma=self.config.lr_gamma,
            device=self.config.device,
            seed=self.config.seed,
            log_gradient_norms=self.config.log_gradient_norms,
            log_dir=self.log_dir
        )

        # 4. Run Training
        logger.info("Starting training loop...")
        # run_training returns a dict with 'model', 'history', 'metrics'
        training_output = run_training(
            model=model,
            train_data=train_data,
            test_data=test_data, # Pass test data for early stopping/evaluation
            config=training_config
        )

        trained_model = training_output['model']
        history = training_output['history']

        end_time = time.time()
        total_time = end_time - start_time

        # 5. Calculate MAE
        logger.info("Calculating final MAE on train and test sets...")

        # Helper to calculate MAE on a dataset using the trained model
        def evaluate_mae(model, data, device):
            model.eval()
            with torch.no_grad():
                X = torch.tensor(data['X'], dtype=torch.float32).to(device)
                y = torch.tensor(data['y'], dtype=torch.float32).to(device)
                pred = model(X)
                mae = calculate_mae(pred, y)
            return mae

        train_mae = evaluate_mae(trained_model, train_data, self.config.device)
        test_mae = evaluate_mae(trained_model, test_data, self.config.device)

        # Round to 4 decimal places
        train_mae = round(float(train_mae), 4)
        test_mae = round(float(test_mae), 4)

        # 6. Calculate Degradation
        if train_mae > 0:
            degradation_pct = ((test_mae - train_mae) / train_mae) * 100
        else:
            degradation_pct = 0.0
        degradation_pct = round(float(degradation_pct), 4)

        # 7. Constraint Check (Warning only)
        if degradation_pct >= 10.0:
            logger.warning(f"Degradation exceeds 10% threshold: {degradation_pct}%")
        else:
            logger.info(f"Degradation within threshold: {degradation_pct}%")

        # 8. Create Result Object
        result = ExperimentResult(
            config_name=self.config.name,
            train_mae=train_mae,
            test_mae=test_mae,
            degradation_pct=degradation_pct,
            total_time_seconds=round(total_time, 2),
            epoch_count=self.config.epochs,
            device=self.config.device,
            seed=self.config.seed,
            params_count=params_count
        )

        # 9. Save JSON Artifact
        metrics_path = os.path.join(self.output_dir, "baseline_metrics.json")
        metrics_dict = {
            "train_mae": result.train_mae,
            "test_mae": result.test_mae,
            "degradation_pct": result.degradation_pct
        }

        with open(metrics_path, 'w') as f:
            json.dump(metrics_dict, f, indent=2)

        logger.info(f"Metrics saved to {metrics_path}")
        logger.info(f"Train MAE: {train_mae}, Test MAE: {test_mae}, Degradation: {degradation_pct}%")

        return result


def main():
    """Entry point for running the baseline experiment."""
    config = ExperimentConfig(
        name="baseline_lorenz_poly",
        seed=42,
        hidden_dim=64,
        num_heads=4,
        num_layers=2,
        batch_size=32,
        epochs=10,
        learning_rate=1e-3,
        device="cpu"
    )

    runner = BaselineRunner(config)
    result = runner.run_and_record_metrics()
    return result


if __name__ == "__main__":
    main()
