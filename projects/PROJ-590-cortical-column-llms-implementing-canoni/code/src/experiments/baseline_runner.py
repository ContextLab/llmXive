import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any

import torch
import torch.nn as nn

# Import from project API surface
from src.models.baseline_transformer import BaselineTransformer
from src.data.benchmarks import generate_training_data, generate_test_data, verify_independence
from src.training.trainer import TrainingConfig, run_training, calculate_mae

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class ExperimentConfig:
    """Configuration for a baseline experiment."""
    seed: int = 42
    hidden_dim: int = 64
    num_layers: int = 2
    num_heads: int = 4
    max_epochs: int = 10
    batch_size: int = 32
    learning_rate: float = 1e-3
    lr_scheduler_type: str = "constant"
    weight_decay: float = 0.0
    gradient_clip_val: float = 1.0
    device: str = "cpu"
    output_dir: str = "data/results"


@dataclass
class ExperimentResult:
    """Result of a baseline experiment."""
    train_mae: float = 0.0
    test_mae: float = 0.0
    degradation_pct: float = 0.0
    passed: bool = False
    total_time: float = 0.0
    seed: int = 0
    config: Dict[str, Any] = field(default_factory=dict)


class BaselineRunner:
    """
    Orchestrates the baseline Transformer training and evaluation pipeline.
    Handles data generation, model instantiation, training loop execution,
    and metric recording as per T015.
    """

    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.output_dir = config.output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def _build_model(self) -> BaselineTransformer:
        """Instantiates the baseline Transformer model."""
        logger.info(f"Building BaselineTransformer with hidden_dim={self.config.hidden_dim}, "
                    f"num_layers={self.config.num_layers}, num_heads={self.config.num_heads}")
        
        model = BaselineTransformer(
            hidden_dim=self.config.hidden_dim,
            num_layers=self.config.num_layers,
            num_heads=self.config.num_heads,
            d_model=self.config.hidden_dim, 
            device=self.config.device
        )
        return model.to(self.config.device)

    def _generate_data(self):
        """Generates training (Lorenz) and test (Polynomials) data."""
        logger.info("Generating training data (Lorenz Attractor)...")
        train_data = generate_training_data(seed=self.config.seed)
        
        logger.info("Generating test data (Polynomial Surfaces)...")
        test_data = generate_test_data(seed=self.config.seed + 1000) # Distinct seed for independence
        
        # Verify independence as per T008b
        try:
            verify_independence(train_data, test_data)
            logger.info("Data independence verified (KS test passed).")
        except ValueError as e:
            logger.error(f"Data independence check failed: {e}")
            raise

        return train_data, test_data

    def run_and_record_metrics(self) -> ExperimentResult:
        """
        Executes the full baseline pipeline and records metrics to data/results/baseline_metrics.json.
        
        Logic:
        1. Generate training (Lorenz) and test (Polynomials) data.
        2. Instantiate BaselineTransformer.
        3. Train on training set.
        4. Evaluate on training set (train_mae) and test set (test_mae).
        5. Calculate degradation_pct = ((test_mae - train_mae) / train_mae) * 100.
        6. Determine passed = (degradation_pct < 10.0).
        7. Write JSON to data/results/baseline_metrics.json.
        
        Returns:
            ExperimentResult object with calculated metrics.
        """
        start_time = time.time()
        logger.info("Starting baseline experiment run_and_record_metrics...")

        # 1. Data Generation
        train_data, test_data = self._generate_data()

        # 2. Model Instantiation
        model = self._build_model()

        # 3. Training Configuration
        training_config = TrainingConfig(
            seed=self.config.seed,
            max_epochs=self.config.max_epochs,
            batch_size=self.config.batch_size,
            learning_rate=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
            gradient_clip_val=self.config.gradient_clip_val,
            device=self.config.device,
            log_dir="data/logs", # Ensure logs are written
            use_homeostasis=False # Baseline does not use homeostasis
        )

        # 4. Training Execution
        # run_training expects data in a specific format (X, y). 
        # We assume generate_* functions return (X, y) tuples or similar compatible structures.
        # If they return raw arrays, we need to wrap them.
        # For this implementation, we assume the trainer can handle the data directly 
        # or we adapt the trainer call. Given the API surface, we call run_training 
        # and pass the data.
        
        logger.info(f"Training model for {self.config.max_epochs} epochs...")
        
        # We need to adapt the trainer to accept our generated data.
        # The trainer usually expects a DataLoader. We will create a simple wrapper 
        # or pass the data if the trainer is flexible.
        # For T015, we assume the trainer can run on the raw numpy arrays 
        # converted to torch tensors if necessary.
        
        # Convert data to tensors for the trainer
        X_train = torch.tensor(train_data[0], dtype=torch.float32).to(self.config.device)
        y_train = torch.tensor(train_data[1], dtype=torch.float32).to(self.config.device)
        X_test = torch.tensor(test_data[0], dtype=torch.float32).to(self.config.device)
        y_test = torch.tensor(test_data[1], dtype=torch.float32).to(self.config.device)

        # Run training loop manually or via helper to get final model state
        # We use run_training which returns the trained model and metrics
        trained_model, train_metrics = run_training(
            model=model,
            config=training_config,
            train_data=(X_train, y_train),
            test_data=(X_test, y_test) # Pass test data for evaluation during/after training
        )

        # 5. Evaluation
        # Calculate MAE on training set
        train_mae = calculate_mae(trained_model, X_train, y_train)
        # Calculate MAE on test set
        test_mae = calculate_mae(trained_model, X_test, y_test)

        # Round to 4 decimal places
        train_mae = round(train_mae, 4)
        test_mae = round(test_mae, 4)

        # 6. Calculate Degradation
        if train_mae > 0:
            degradation_pct = ((test_mae - train_mae) / train_mae) * 100
        else:
            degradation_pct = 0.0
        
        degradation_pct = round(degradation_pct, 4)

        # 7. Determine Pass/Fail
        passed = degradation_pct < 10.0

        total_time = time.time() - start_time

        result = ExperimentResult(
            train_mae=train_mae,
            test_mae=test_mae,
            degradation_pct=degradation_pct,
            passed=passed,
            total_time=total_time,
            seed=self.config.seed,
            config=asdict(self.config)
        )

        # 8. Write Artifact
        output_path = os.path.join(self.output_dir, "baseline_metrics.json")
        with open(output_path, 'w') as f:
            json.dump(asdict(result), f, indent=2)
        
        logger.info(f"Metrics written to {output_path}")
        logger.info(f"Result: train_mae={train_mae}, test_mae={test_mae}, degradation={degradation_pct}%, passed={passed}")

        return result


def main():
    """Entry point for running the baseline experiment from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="Run Baseline Experiment (T015)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--hidden-dim", type=int, default=64, help="Hidden dimension")
    parser.add_argument("--num-layers", type=int, default=2, help="Number of transformer layers")
    parser.add_argument("--num-heads", type=int, default=4, help="Number of attention heads")
    parser.add_argument("--max-epochs", type=int, default=10, help="Max training epochs")
    parser.add_argument("--output-dir", type=str, default="data/results", help="Output directory for metrics")
    
    args = parser.parse_args()

    config = ExperimentConfig(
        seed=args.seed,
        hidden_dim=args.hidden_dim,
        num_layers=args.num_layers,
        num_heads=args.num_heads,
        max_epochs=args.max_epochs,
        output_dir=args.output_dir
    )

    runner = BaselineRunner(config)
    runner.run_and_record_metrics()


if __name__ == "__main__":
    main()
