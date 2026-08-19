import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional

import torch
import torch.nn as nn
import torch.optim as optim

from src.data.benchmarks import generate_training_data, generate_test_data
from src.models.baseline_transformer import BaselineTransformer, create_baseline_model
from src.training.trainer import TrainingConfig, calculate_mae, run_training, evaluate
from src.training.homeostasis import log_gradient_norms

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ExperimentConfig:
    name: str = "baseline_experiment"
    hidden_dim: int = 64
    num_layers: int = 4
    num_heads: int = 4
    seq_len: int = 128
    batch_size: int = 32
    epochs: int = 10
    learning_rate: float = 1e-3
    seed: int = 42
    log_gradients: bool = True
    gradient_log_path: str = "data/logs/gradient_norms.json"

@dataclass
class ExperimentResult:
    name: str
    train_mae: float
    test_mae: float
    degradation_pct: float
    passed: bool
    duration_seconds: float
    config: Dict[str, Any] = field(default_factory=dict)

class BaselineRunner:
    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.device = torch.device("cpu")
        torch.manual_seed(config.seed)

    def run_and_record_metrics(self, output_path: str = "data/results/baseline_metrics.json") -> ExperimentResult:
        """
        Runs the baseline model on training (Lorenz) and test (Polynomials) sets.
        Calculates MAE for both, computes degradation percentage, and records results.
        """
        logger.info(f"Starting baseline experiment: {self.config.name}")
        start_time = time.time()

        # Generate distinct datasets as per T008a/T008b
        logger.info("Generating training data (Lorenz)...")
        train_data = generate_training_data(n_samples=5000, seq_len=self.config.seq_len, seed=self.config.seed)
        logger.info("Generating test data (Polynomials)...")
        test_data = generate_test_data(n_samples=1000, seq_len=self.config.seq_len, seed=self.config.seed + 1)

        # Verify independence (T008b)
        from src.data.benchmarks import verify_independence
        try:
            verify_independence(train_data, test_data)
            logger.info("Data independence verified.")
        except ValueError as e:
            logger.warning(f"Data independence check failed: {e}")

        # Create model
        logger.info("Creating baseline model...")
        model = create_baseline_model(
            hidden_dim=self.config.hidden_dim,
            num_layers=self.config.num_layers,
            num_heads=self.config.num_heads,
            input_dim=train_data.shape[2],
            output_dim=train_data.shape[2]
        )
        model.to(self.device)

        # Prepare data loaders
        train_tensor = torch.FloatTensor(train_data)
        test_tensor = torch.FloatTensor(test_data)

        train_dataset = torch.utils.data.TensorDataset(train_tensor, train_tensor)
        test_dataset = torch.utils.data.TensorDataset(test_tensor, test_tensor)

        train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=self.config.batch_size, shuffle=True)
        test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=self.config.batch_size, shuffle=False)

        optimizer = optim.Adam(model.parameters(), lr=self.config.learning_rate)
        criterion = nn.MSELoss()

        # Training configuration
        training_config = TrainingConfig(
            epochs=self.config.epochs,
            lr=self.config.learning_rate,
            clip_grad_norm=1.0,
            log_interval=1,
            log_gradients=self.config.log_gradients,
            gradient_log_path=self.config.gradient_log_path
        )

        # Train
        logger.info("Training baseline model...")
        train_metrics = run_training(
            model=model,
            train_loader=train_loader,
            test_loader=test_loader,
            optimizer=optimizer,
            criterion=criterion,
            config=training_config,
            device=self.device
        )

        # Evaluate on test set
        logger.info("Evaluating on test set...")
        test_mae, _ = evaluate(model, test_loader, criterion, self.device)
        
        # Ensure we have a valid train_mae (fallback to last epoch if not stored in metrics dict directly)
        train_mae = train_metrics.get('final_train_mae', train_metrics.get('train_mae', 0.0))

        # Calculate degradation
        if train_mae > 0.0:
            degradation_pct = ((test_mae - train_mae) / train_mae) * 100.0
        else:
            degradation_pct = 0.0

        # Determine pass status (passed if degradation < 10%)
        passed = degradation_pct < 10.0

        duration = time.time() - start_time

        result = ExperimentResult(
            name=self.config.name,
            train_mae=round(float(train_mae), 4),
            test_mae=round(float(test_mae), 4),
            degradation_pct=round(float(degradation_pct), 4),
            passed=passed,
            duration_seconds=round(float(duration), 2),
            config=asdict(self.config)
        )

        # Write output artifact
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(asdict(result), f, indent=2)

        logger.info(f"Results written to {output_path}")
        logger.info(f"Train MAE: {result.train_mae}, Test MAE: {result.test_mae}, Degradation: {result.degradation_pct}%")
        logger.info(f"Test Passed: {result.passed}")

        return result

def main():
    config = ExperimentConfig(
        name="baseline_lorenz_poly",
        hidden_dim=64,
        num_layers=4,
        num_heads=4,
        seq_len=128,
        batch_size=32,
        epochs=10,
        learning_rate=1e-3,
        seed=42
    )
    runner = BaselineRunner(config)
    runner.run_and_record_metrics(output_path="data/results/baseline_metrics.json")

if __name__ == "__main__":
    main()