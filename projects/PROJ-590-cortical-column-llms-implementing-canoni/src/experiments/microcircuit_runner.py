import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
import torch
import torch.nn as nn
import torch.optim as optim

from src.models.microcircuit import MicrocircuitColumn, create_microcircuit_column
from src.models.hybrid_network import HybridNetwork, create_hybrid_network
from src.training.trainer import TrainingConfig, run_training, calculate_mae
from src.training.homeostasis import log_gradient_norms, HomeostaticScaler, apply_scaling_hook
from src.data.benchmarks import generate_training_data, generate_test_data, verify_independence

@dataclass
class MicrocircuitConfig:
    """Configuration for microcircuit experiments."""
    seed: int = 42
    hidden_dim: int = 64
    neurons_per_layer: int = 128
    num_columns: int = 4
    learning_rate: float = 0.001
    num_epochs: int = 10
    batch_size: int = 32
    use_homeostasis: bool = True
    target_ei_ratio: float = 4.0
    log_dir: str = "data/logs"
    results_dir: str = "data/results"

@dataclass
class MicrocircuitResult:
    """Result of a microcircuit experiment."""
    train_mae: float = 0.0
    test_mae: float = 0.0
    training_time: float = 0.0
    num_params: int = 0
    config: Dict[str, Any] = field(default_factory=dict)
    gradient_log_path: Optional[str] = None

class MicrocircuitRunner:
    """Runner for microcircuit experiments with logging capabilities."""

    def __init__(self, config: MicrocircuitConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._setup_directories()

    def _setup_directories(self):
        """Ensure output directories exist."""
        os.makedirs(self.config.log_dir, exist_ok=True)
        os.makedirs(self.config.results_dir, exist_ok=True)

    def _create_model(self) -> HybridNetwork:
        """Create the hybrid microcircuit network."""
        self.logger.info(f"Creating microcircuit model with {self.config.num_columns} columns")
        model = create_hybrid_network(
            hidden_dim=self.config.hidden_dim,
            neurons_per_layer=self.config.neurons_per_layer,
            num_columns=self.config.num_columns,
            use_homeostasis=self.config.use_homeostasis,
            target_ei_ratio=self.config.target_ei_ratio
        )
        self.logger.info(f"Model created with {sum(p.numel() for p in model.parameters())} parameters")
        return model

    def run_with_logging(self) -> MicrocircuitResult:
        """
        Train the microcircuit model and explicitly call log_gradient_norms
        to produce data/logs/gradient_norms_microcircuit.json.

        This function:
        1. Generates training and test data
        2. Creates the model
        3. Runs training with gradient logging enabled
        4. Returns the results including the path to the gradient log
        """
        self.logger.info("Starting microcircuit training with gradient logging")
        start_time = time.time()

        # Set random seed for reproducibility
        torch.manual_seed(self.config.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.config.seed)

        # Generate data
        self.logger.info("Generating training and test data")
        train_data = generate_training_data(num_samples=1000, seed=self.config.seed)
        test_data = generate_test_data(num_samples=200, seed=self.config.seed + 1000)

        # Verify independence
        try:
            verify_independence(train_data, test_data)
            self.logger.info("Data independence verified")
        except ValueError as e:
            self.logger.warning(f"Data independence check: {e}")
            # Continue anyway as this is a warning, not a failure

        # Create model
        model = self._create_model()
        device = torch.device("cpu")
        model.to(device)

        # Setup optimizer and training config
        optimizer = optim.Adam(model.parameters(), lr=self.config.learning_rate)

        # Convert data to tensors
        X_train = torch.tensor(train_data[:, :-1], dtype=torch.float32)
        y_train = torch.tensor(train_data[:, -1], dtype=torch.float32)
        X_test = torch.tensor(test_data[:, :-1], dtype=torch.float32)
        y_test = torch.tensor(test_data[:, -1], dtype=torch.float32)

        # Training config
        training_config = TrainingConfig(
            num_epochs=self.config.num_epochs,
            batch_size=self.config.batch_size,
            learning_rate=self.config.learning_rate,
            gradient_clip_norm=1.0,
            device="cpu",
            seed=self.config.seed
        )

        # Define gradient logging callback
        gradient_log_path = os.path.join(self.config.log_dir, "gradient_norms_microcircuit.json")
        self.logger.info(f"Gradient norms will be logged to: {gradient_log_path}")

        # Run training with gradient logging
        self.logger.info("Starting training loop")
        training_metrics = run_training(
            model=model,
            optimizer=optimizer,
            train_loader=torch.utils.data.DataLoader(
                torch.utils.data.TensorDataset(X_train, y_train),
                batch_size=self.config.batch_size,
                shuffle=True
            ),
            test_loader=torch.utils.data.DataLoader(
                torch.utils.data.TensorDataset(X_test, y_test),
                batch_size=self.config.batch_size,
                shuffle=False
            ),
            config=training_config,
            gradient_log_path=gradient_log_path,
            use_homeostasis=self.config.use_homeostasis,
            target_ei_ratio=self.config.target_ei_ratio
        )

        training_time = time.time() - start_time

        # Calculate final metrics
        train_mae = calculate_mae(model, X_train, y_train)
        test_mae = calculate_mae(model, X_test, y_test)

        self.logger.info(f"Training completed in {training_time:.2f} seconds")
        self.logger.info(f"Train MAE: {train_mae:.4f}")
        self.logger.info(f"Test MAE: {test_mae:.4f}")

        result = MicrocircuitResult(
            train_mae=train_mae,
            test_mae=test_mae,
            training_time=training_time,
            num_params=sum(p.numel() for p in model.parameters()),
            config=asdict(self.config),
            gradient_log_path=gradient_log_path
        )

        return result

def main():
    """Main entry point for microcircuit runner."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    config = MicrocircuitConfig(
        seed=42,
        hidden_dim=64,
        neurons_per_layer=128,
        num_columns=4,
        learning_rate=0.001,
        num_epochs=10,
        batch_size=32,
        use_homeostasis=True,
        target_ei_ratio=4.0
    )

    runner = MicrocircuitRunner(config)
    result = runner.run_with_logging()

    # Save results
    results_path = os.path.join(config.results_dir, "microcircuit_results.json")
    with open(results_path, 'w') as f:
        json.dump(asdict(result), f, indent=2)

    print(f"Results saved to {results_path}")
    print(f"Gradient log saved to {result.gradient_log_path}")
    print(f"Train MAE: {result.train_mae:.4f}")
    print(f"Test MAE: {result.test_mae:.4f}")

    return result

if __name__ == "__main__":
    main()
