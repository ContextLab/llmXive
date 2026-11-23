"""
Microcircuit Runner: Trains the HybridNetwork (Microcircuit-based) and logs gradients.

This module implements the training loop for the cortical column microcircuit model,
integrating homeostatic scaling and explicit gradient logging as required by T011d.
It depends on T012 (trainer), T019 (HybridNetwork), and T010b (log_gradient_norms).
"""

import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Dict, Any

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

# Local imports (must match API surface)
from src.models.hybrid_network import HybridNetwork, create_hybrid_network
from src.training.trainer import TrainingConfig, run_training, calculate_mae, train_epoch, evaluate
from src.training.homeostasis import log_gradient_norms, HomeostaticScaler, apply_scaling_hook
from src.data.benchmarks import generate_training_data, generate_test_data, verify_independence

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class MicrocircuitConfig:
    """Configuration for the microcircuit experiment."""
    hidden_dim: int = 64
    num_layers: int = 4
    neurons_per_layer: int = 128
    learning_rate: float = 1e-3
    epochs: int = 10
    batch_size: int = 32
    seed: int = 42
    target_ei_ratio: float = 4.0
    gradient_log_path: str = "data/logs/gradient_norms_microcircuit.json"
    metrics_path: str = "data/results/microcircuit_metrics.json"

@dataclass
class MicrocircuitResult:
    """Result of a microcircuit training run."""
    train_mae: float
    test_mae: float
    total_time: float
    epochs_completed: int
    gradient_log_path: str
    metrics_path: str

class MicrocircuitRunner:
    """
    Orchestrates the training of the HybridNetwork (Microcircuit) model.
    
    Implements T011d: Trains the model and explicitly calls log_gradient_norms
    to produce data/logs/gradient_norms_microcircuit.json.
    """

    def __init__(self, config: MicrocircuitConfig):
        self.config = config
        self.device = torch.device("cpu") # Enforce CPU as per project constraints
        torch.manual_seed(config.seed)
        
        # Ensure output directories exist
        Path(config.gradient_log_path).parent.mkdir(parents=True, exist_ok=True)
        Path(config.metrics_path).parent.mkdir(parents=True, exist_ok=True)

    def _generate_data(self):
        """Generate synthetic training and test data."""
        logger.info("Generating synthetic data...")
        train_data = generate_training_data(seed=self.config.seed)
        test_data = generate_test_data(seed=self.config.seed + 1)
        
        # Verify independence (T008b)
        try:
            verify_independence(train_data, test_data)
            logger.info("Data independence verified.")
        except ValueError as e:
            logger.error(f"Data independence check failed: {e}")
            raise

        # Convert to tensors
        X_train = torch.tensor(train_data[:, :-1], dtype=torch.float32)
        y_train = torch.tensor(train_data[:, -1], dtype=torch.float32).unsqueeze(1)
        X_test = torch.tensor(test_data[:, :-1], dtype=torch.float32)
        y_test = torch.tensor(test_data[:, -1], dtype=torch.float32).unsqueeze(1)

        train_dataset = TensorDataset(X_train, y_train)
        test_dataset = TensorDataset(X_test, y_test)

        train_loader = DataLoader(train_dataset, batch_size=self.config.batch_size, shuffle=True)
        test_loader = DataLoader(test_dataset, batch_size=self.config.batch_size, shuffle=False)

        return train_loader, test_loader

    def run_with_logging(self) -> MicrocircuitResult:
        """
        Train the microcircuit model and log gradient norms.
        
        This is the core implementation for T011d.
        """
        logger.info(f"Starting Microcircuit training with config: {self.config}")
        
        # 1. Generate Data
        train_loader, test_loader = self._generate_data()

        # 2. Initialize Model (T019)
        logger.info("Initializing HybridNetwork (Microcircuit)...")
        model = create_hybrid_network(
            input_dim=train_loader.dataset.tensors[0].shape[1],
            hidden_dim=self.config.hidden_dim,
            num_layers=self.config.num_layers,
            neurons_per_layer=self.config.neurons_per_layer,
        ).to(self.device)

        # 3. Setup Optimizer and Loss
        optimizer = optim.Adam(model.parameters(), lr=self.config.learning_rate)
        criterion = nn.MSELoss()

        # 4. Homeostatic Scaler (T010c, T018a)
        scaler = HomeostaticScaler(
            model=model,
            target_ratio=self.config.target_ei_ratio,
            decay_rate=0.01
        )

        # 5. Training Loop
        start_time = time.time()
        epochs_completed = 0
        
        # Initialize log file
        log_file_path = Path(self.config.gradient_log_path)
        if log_file_path.exists():
            log_file_path.unlink() # Clear previous run

        logger.info("Beginning training loop...")
        
        for epoch in range(self.config.epochs):
            model.train()
            epoch_loss = 0.0
            
            for batch_x, batch_y in train_loader:
                batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device)
                
                optimizer.zero_grad()
                outputs = model(batch_x)
                loss = criterion(outputs, batch_y)
                loss.backward()
                
                # Gradient Clipping (T012)
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                
                # T011d: Explicitly call log_gradient_norms
                # This populates data/logs/gradient_norms_microcircuit.json
                log_gradient_norms(model, step=epoch)
                
                optimizer.step()
                
                # Apply homeostatic scaling (T018a)
                apply_scaling_hook(optimizer, step=epoch)
                
                epoch_loss += loss.item()
            
            avg_loss = epoch_loss / len(train_loader)
            epochs_completed += 1
            logger.info(f"Epoch {epoch+1}/{self.config.epochs}, Loss: {avg_loss:.4f}")

            # Optional: Evaluate per epoch to ensure stability
            if (epoch + 1) % 2 == 0:
                model.eval()
                with torch.no_grad():
                    test_outputs = model(test_loader.dataset.tensors[0].to(self.device))
                    test_loss = criterion(test_outputs, test_loader.dataset.tensors[1].to(self.device))
                    logger.info(f"  Epoch {epoch+1} Test Loss: {test_loss.item():.4f}")

        total_time = time.time() - start_time

        # 6. Final Evaluation
        model.eval()
        with torch.no_grad():
            train_outputs = model(train_loader.dataset.tensors[0].to(self.device))
            train_mae = calculate_mae(train_outputs, train_loader.dataset.tensors[1].to(self.device))
            
            test_outputs = model(test_loader.dataset.tensors[0].to(self.device))
            test_mae = calculate_mae(test_outputs, test_loader.dataset.tensors[1].to(self.device))

        # 7. Record Metrics
        result = MicrocircuitResult(
            train_mae=train_mae,
            test_mae=test_mae,
            total_time=total_time,
            epochs_completed=epochs_completed,
            gradient_log_path=self.config.gradient_log_path,
            metrics_path=self.config.metrics_path
        )

        # Save metrics to JSON
        metrics = {
            "train_mae": round(result.train_mae, 4),
            "test_mae": round(result.test_mae, 4),
            "total_time": round(result.total_time, 2),
            "epochs": result.epochs_completed,
            "gradient_log": result.gradient_log_path
        }
        
        with open(self.config.metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Training complete. Metrics saved to {self.config.metrics_path}")
        logger.info(f"Gradient norms logged to {self.config.gradient_log_path}")

        return result

def main():
    """Entry point for the microcircuit runner script."""
    config = MicrocircuitConfig(
        hidden_dim=64,
        num_layers=4,
        neurons_per_layer=128,
        epochs=10, # Small epoch count for CI/CD speed, sufficient for T011d artifact generation
        learning_rate=1e-3,
        seed=42
    )
    
    runner = MicrocircuitRunner(config)
    result = runner.run_with_logging()
    
    print(f"Microcircuit Training Finished.")
    print(f"Train MAE: {result.train_mae:.4f}")
    print(f"Test MAE: {result.test_mae:.4f}")
    print(f"Time: {result.total_time:.2f}s")
    print(f"Gradient Log: {result.gradient_log_path}")

if __name__ == "__main__":
    main()
