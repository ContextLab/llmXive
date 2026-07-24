"""
Microcircuit Runner for Hybrid Model Training

Implements training and evaluation of the HybridNetwork (Microcircuit-based)
on the same synthetic tasks used for the baseline Transformer.
"""
import json
import logging
import os
import sys
import time
import argparse
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any

import torch
import torch.nn as nn
import numpy as np

# Import from project modules (matching API surface)
from src.models.hybrid_network import create_hybrid_network, HybridNetwork
from src.training.trainer import TrainingConfig, TrainingMetrics, run_training, calculate_mae
from src.training.homeostasis import HomeostasisConfig, HomeostaticScaler
from src.data.benchmarks import (
    generate_synthetic_dataset,
    LorenzConfig,
    FourierConfig,
    PolynomialConfig
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class MicrocircuitConfig:
    """Configuration for the Microcircuit experiment."""
    # Model parameters
    num_columns: int = 4
    hidden_dim: int = 64
    num_layers: int = 4
    dropout: float = 0.1
    
    # Training parameters
    learning_rate: float = 1e-3
    batch_size: int = 32
    num_epochs: int = 50
    weight_decay: float = 1e-4
    max_grad_norm: float = 1.0
    
    # Data parameters
    sequence_length: int = 50
    noise_level: float = 0.01
    
    # Homeostasis parameters
    target_ei_ratio: float = 4.0
    homeostasis_frequency: int = 10  # Apply every N steps
    
    # Experiment parameters
    seed: int = 42
    output_dir: str = "data/results"
    experiment_name: str = "microcircuit_experiment"

@dataclass
class ExperimentResult:
    """Result container for a microcircuit experiment."""
    experiment_name: str
    config: Dict[str, Any]
    metrics: Dict[str, float]
    training_time_seconds: float
    peak_memory_mb: float
    model_params: int
    output_file: str

class MicrocircuitRunner:
    """
    Orchestrates training and evaluation of the HybridNetwork on synthetic tasks.
    
    This runner mirrors the BaselineRunner structure but uses the Microcircuit
    architecture instead of the standard Transformer.
    """
    
    def __init__(self, config: MicrocircuitConfig):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        # Set random seeds for reproducibility
        torch.manual_seed(config.seed)
        np.random.seed(config.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(config.seed)
        
        # Create output directory
        os.makedirs(config.output_dir, exist_ok=True)
        
        # Initialize homeostatic scaler if needed
        self.homeostasis_config = HomeostasisConfig(
            target_ei_ratio=config.target_ei_ratio,
            frequency=config.homeostasis_frequency
        )
    
    def _generate_task_data(self, task_type: str, split: str = "train"):
        """Generate synthetic data for a specific task type."""
        logger.info(f"Generating {task_type} data for {split} split")
        
        if task_type == "lorenz":
            config = LorenzConfig(
                sequence_length=self.config.sequence_length,
                noise_level=self.config.noise_level,
                seed=self.config.seed
            )
        elif task_type == "fourier":
            config = FourierConfig(
                sequence_length=self.config.sequence_length,
                noise_level=self.config.noise_level,
                seed=self.config.seed
            )
        elif task_type == "polynomial":
            config = PolynomialConfig(
                sequence_length=self.config.sequence_length,
                noise_level=self.config.noise_level,
                seed=self.config.seed
            )
        else:
            raise ValueError(f"Unknown task type: {task_type}")
        
        data = generate_synthetic_dataset(config, split=split)
        return data
    
    def _prepare_dataloader(self, data: Dict[str, np.ndarray], batch_size: int):
        """Convert numpy data to PyTorch dataloader."""
        X = torch.FloatTensor(data["X"])
        y = torch.FloatTensor(data["y"])
        
        dataset = torch.utils.data.TensorDataset(X, y)
        dataloader = torch.utils.data.DataLoader(
            dataset, 
            batch_size=batch_size, 
            shuffle=True,
            drop_last=True
        )
        return dataloader
    
    def run_experiment(self, task_type: str = "lorenz") -> ExperimentResult:
        """
        Run a complete training and evaluation experiment.
        
        Args:
            task_type: Type of synthetic task ("lorenz", "fourier", "polynomial")
        
        Returns:
            ExperimentResult containing metrics and configuration
        """
        logger.info(f"Starting {task_type} experiment with Microcircuit model")
        
        start_time = time.time()
        
        # Generate data
        train_data = self._generate_task_data(task_type, split="train")
        val_data = self._generate_task_data(task_type, split="val")
        test_data = self._generate_task_data(task_type, split="test")
        
        # Create dataloaders
        train_loader = self._prepare_dataloader(train_data, self.config.batch_size)
        val_loader = self._prepare_dataloader(val_data, self.config.batch_size)
        test_loader = self._prepare_dataloader(test_data, self.config.batch_size)
        
        # Create model
        model = create_hybrid_network(
            num_columns=self.config.num_columns,
            hidden_dim=self.config.hidden_dim,
            num_layers=self.config.num_layers,
            dropout=self.config.dropout,
            input_dim=train_data["X"].shape[-1],
            output_dim=train_data["y"].shape[-1]
        ).to(self.device)
        
        num_params = sum(p.numel() for p in model.parameters())
        logger.info(f"Model created with {num_params:,} parameters")
        
        # Create training config
        training_config = TrainingConfig(
            learning_rate=self.config.learning_rate,
            batch_size=self.config.batch_size,
            num_epochs=self.config.num_epochs,
            weight_decay=self.config.weight_decay,
            max_grad_norm=self.config.max_grad_norm,
            device=str(self.device),
            seed=self.config.seed,
            homeostasis_config=self.homeostasis_config
        )
        
        # Train model
        logger.info("Starting training...")
        metrics = run_training(
            model=model,
            train_loader=train_loader,
            val_loader=val_loader,
            config=training_config
        )
        
        # Evaluate on test set
        logger.info("Evaluating on test set...")
        test_mae = calculate_mae(model, test_loader, self.device)
        metrics["test_mae"] = float(test_mae)
        
        end_time = time.time()
        training_time = end_time - start_time
        
        # Get memory usage (approximate)
        if torch.cuda.is_available():
            peak_memory = torch.cuda.max_memory_allocated() / (1024 * 1024)
        else:
            # Estimate from process (less accurate on CPU)
            import psutil
            process = psutil.Process(os.getpid())
            peak_memory = process.memory_info().rss / (1024 * 1024)
        
        # Prepare result
        result = ExperimentResult(
            experiment_name=f"{self.config.experiment_name}_{task_type}",
            config=asdict(self.config),
            metrics=metrics,
            training_time_seconds=training_time,
            peak_memory_mb=peak_memory,
            model_params=num_params,
            output_file=""
        )
        
        # Save results
        output_filename = f"{result.experiment_name}_results.json"
        output_path = os.path.join(self.config.output_dir, output_filename)
        
        result_dict = {
            "experiment_name": result.experiment_name,
            "config": result.config,
            "metrics": result.metrics,
            "training_time_seconds": result.training_time_seconds,
            "peak_memory_mb": result.peak_memory_mb,
            "model_params": result.model_params
        }
        
        with open(output_path, "w") as f:
            json.dump(result_dict, f, indent=2)
        
        result.output_file = output_path
        logger.info(f"Results saved to {output_path}")
        
        return result

def main():
    """Main entry point for the microcircuit runner."""
    parser = argparse.ArgumentParser(description="Run Microcircuit experiment")
    parser.add_argument("--task", type=str, default="lorenz", 
                      choices=["lorenz", "fourier", "polynomial"],
                      help="Task type to run")
    parser.add_argument("--num-columns", type=int, default=4,
                      help="Number of cortical columns")
    parser.add_argument("--hidden-dim", type=int, default=64,
                      help="Hidden dimension size")
    parser.add_argument("--num-layers", type=int, default=4,
                      help="Number of layers")
    parser.add_argument("--epochs", type=int, default=50,
                      help="Number of training epochs")
    parser.add_argument("--seed", type=int, default=42,
                      help="Random seed")
    parser.add_argument("--output-dir", type=str, default="data/results",
                      help="Output directory for results")
    
    args = parser.parse_args()
    
    config = MicrocircuitConfig(
        num_columns=args.num_columns,
        hidden_dim=args.hidden_dim,
        num_layers=args.num_layers,
        num_epochs=args.epochs,
        seed=args.seed,
        output_dir=args.output_dir,
        experiment_name=f"microcircuit_{args.task}"
    )
    
    runner = MicrocircuitRunner(config)
    result = runner.run_experiment(task_type=args.task)
    
    print(f"\nExperiment completed:")
    print(f"  Task: {args.task}")
    print(f"  Test MAE: {result.metrics['test_mae']:.6f}")
    print(f"  Training time: {result.training_time_seconds:.2f}s")
    print(f"  Peak memory: {result.peak_memory_mb:.2f} MB")
    print(f"  Results: {result.output_file}")

if __name__ == "__main__":
    main()