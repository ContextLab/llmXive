import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
import torch
import torch.nn as nn
import numpy as np

from src.models.baseline_transformer import create_baseline_transformer, BaselineTransformer
from src.data.benchmarks import generate_training_data, generate_test_data
from src.training.trainer import TrainingConfig, run_training, calculate_mae, TrainingMetrics
from src.training.homeostasis import log_gradient_norms, enforce_ei_ratio

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
    """Configuration for a baseline transformer experiment."""
    experiment_name: str
    model_hidden_dim: int = 256
    model_num_heads: int = 4
    model_num_layers: int = 2
    model_dropout: float = 0.1
    sequence_length: int = 64
    batch_size: int = 32
    learning_rate: float = 1e-4
    num_epochs: int = 100
    weight_decay: float = 1e-4
    gradient_clip_val: float = 1.0
    seed: int = 42
    homeostasis_enabled: bool = True
    output_dir: str = "data/results"

@dataclass
class ExperimentResult:
    """Result of a baseline transformer experiment."""
    experiment_name: str
    config: Dict[str, Any]
    final_train_mae: float
    final_test_mae: float
    total_training_time_seconds: float
    peak_memory_mb: float
    num_parameters: int
    gradient_norms_file: Optional[str]
    model_state_dict_path: Optional[str]
    metrics_history: List[Dict[str, float]] = field(default_factory=list)

class BaselineRunner:
    """
    Runs baseline Transformer training experiments and records metrics.
    Implements T015: run_and_record_metrics method.
    """

    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {self.device}")

        # Ensure output directory exists
        os.makedirs(self.config.output_dir, exist_ok=True)
        os.makedirs('data/logs', exist_ok=True)

    def _create_model(self) -> BaselineTransformer:
        """Create the baseline transformer model."""
        model = create_baseline_transformer(
            hidden_dim=self.config.model_hidden_dim,
            num_heads=self.config.model_num_heads,
            num_layers=self.config.model_num_layers,
            dropout=self.config.model_dropout,
            sequence_length=self.config.sequence_length
        )
        model = model.to(self.device)
        logger.info(f"Created model with {sum(p.numel() for p in model.parameters())} parameters")
        return model

    def _prepare_data(self) -> tuple:
        """Prepare training and test data."""
        logger.info("Generating training data (Lorenz attractor)...")
        train_X, train_y = generate_training_data(
            num_samples=10000,
            sequence_length=self.config.sequence_length,
            seed=self.config.seed
        )

        logger.info("Generating test data (Polynomials/Fourier)...")
        test_X, test_y = generate_test_data(
            num_samples=2000,
            sequence_length=self.config.sequence_length,
            seed=self.config.seed + 1
        )

        # Convert to tensors
        train_X = torch.FloatTensor(train_X).to(self.device)
        train_y = torch.FloatTensor(train_y).to(self.device)
        test_X = torch.FloatTensor(test_X).to(self.device)
        test_y = torch.FloatTensor(test_y).to(self.device)

        logger.info(f"Training data shape: {train_X.shape}")
        logger.info(f"Test data shape: {test_X.shape}")

        return train_X, train_y, test_X, test_y

    def run_and_record_metrics(self) -> ExperimentResult:
        """
        Execute the baseline training loop and record all metrics.
        
        This method:
        1. Creates the model
        2. Generates independent training and test data
        3. Runs the training loop with homeostasis if enabled
        4. Logs gradient norms per batch
        5. Calculates final MAE on train and test sets
        6. Records resource usage and saves results to disk
        
        Returns:
            ExperimentResult: Complete experiment results with paths to saved artifacts.
        """
        start_time = time.time()
        logger.info(f"Starting experiment: {self.config.experiment_name}")

        # Set seed for reproducibility
        torch.manual_seed(self.config.seed)
        np.random.seed(self.config.seed)

        # Create model
        model = self._create_model()

        # Prepare data
        train_X, train_y, test_X, test_y = self._prepare_data()

        # Configure training
        training_config = TrainingConfig(
            batch_size=self.config.batch_size,
            learning_rate=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
            gradient_clip_val=self.config.gradient_clip_val,
            num_epochs=self.config.num_epochs,
            homeostasis_enabled=self.config.homeostasis_enabled,
            log_gradient_norms=True,  # Enable gradient logging for SC-002
            gradient_norms_path=os.path.join('data/logs', f'gradient_norms_{self.config.experiment_name}.json')
        )

        # Run training
        logger.info("Starting training loop...")
        training_metrics: TrainingMetrics = run_training(
            model=model,
            train_X=train_X,
            train_y=train_y,
            test_X=test_X,
            test_y=test_y,
            config=training_config,
            device=self.device
        )

        end_time = time.time()
        total_training_time = end_time - start_time

        # Calculate final MAE
        model.eval()
        with torch.no_grad():
            train_pred = model(train_X)
            test_pred = model(test_X)
            final_train_mae = calculate_mae(train_pred, train_y)
            final_test_mae = calculate_mae(test_pred, test_y)

        logger.info(f"Final Training MAE: {final_train_mae:.6f}")
        logger.info(f"Final Test MAE: {final_test_mae:.6f}")

        # Save model state
        model_state_path = os.path.join(
            self.config.output_dir,
            f"model_{self.config.experiment_name}.pt"
        )
        torch.save(model.state_dict(), model_state_path)
        logger.info(f"Saved model to {model_state_path}")

        # Get peak memory (if psutil available)
        peak_memory_mb = 0.0
        try:
            import psutil
            process = psutil.Process(os.getpid())
            peak_memory_mb = process.memory_info().rss / (1024 * 1024)
        except ImportError:
            logger.warning("psutil not available, skipping memory measurement")

        # Prepare result
        result = ExperimentResult(
            experiment_name=self.config.experiment_name,
            config=asdict(self.config),
            final_train_mae=float(final_train_mae),
            final_test_mae=float(final_test_mae),
            total_training_time_seconds=float(total_training_time),
            peak_memory_mb=float(peak_memory_mb),
            num_parameters=sum(p.numel() for p in model.parameters()),
            gradient_norms_file=training_config.gradient_norms_path if training_config.log_gradient_norms else None,
            model_state_dict_path=model_state_path,
            metrics_history=training_metrics.history
        )

        # Save experiment result to JSON
        result_path = os.path.join(
            self.config.output_dir,
            f"results_{self.config.experiment_name}.json"
        )
        with open(result_path, 'w') as f:
            # Convert dataclass to dict for JSON serialization
            result_dict = {
                'experiment_name': result.experiment_name,
                'config': result.config,
                'final_train_mae': result.final_train_mae,
                'final_test_mae': result.final_test_mae,
                'total_training_time_seconds': result.total_training_time_seconds,
                'peak_memory_mb': result.peak_memory_mb,
                'num_parameters': result.num_parameters,
                'gradient_norms_file': result.gradient_norms_file,
                'model_state_dict_path': result.model_state_dict_path,
                'metrics_history': result.metrics_history
            }
            json.dump(result_dict, f, indent=2)

        logger.info(f"Experiment completed. Results saved to {result_path}")
        return result

def main():
    """Main entry point for running baseline experiments."""
    import argparse

    parser = argparse.ArgumentParser(description='Run baseline transformer experiment')
    parser.add_argument('--name', type=str, default='baseline_run_1', help='Experiment name')
    parser.add_argument('--hidden-dim', type=int, default=256, help='Model hidden dimension')
    parser.add_argument('--num-heads', type=int, default=4, help='Number of attention heads')
    parser.add_argument('--num-layers', type=int, default=2, help='Number of transformer layers')
    parser.add_argument('--epochs', type=int, default=100, help='Number of training epochs')
    parser.add_argument('--lr', type=float, default=1e-4, help='Learning rate')
    parser.add_argument('--no-homeostasis', action='store_true', help='Disable homeostasis')
    
    args = parser.parse_args()

    config = ExperimentConfig(
        experiment_name=args.name,
        model_hidden_dim=args.hidden_dim,
        model_num_heads=args.num_heads,
        model_num_layers=args.num_layers,
        learning_rate=args.lr,
        num_epochs=args.epochs,
        homeostasis_enabled=not args.no_homeostasis
    )

    runner = BaselineRunner(config)
    result = runner.run_and_record_metrics()
    
    print(f"\n=== Experiment Summary ===")
    print(f"Name: {result.experiment_name}")
    print(f"Train MAE: {result.final_train_mae:.6f}")
    print(f"Test MAE: {result.final_test_mae:.6f}")
    print(f"Time: {result.total_training_time_seconds:.2f}s")
    print(f"Parameters: {result.num_parameters}")
    print(f"Results saved to: {result.model_state_dict_path}")

if __name__ == '__main__':
    main()