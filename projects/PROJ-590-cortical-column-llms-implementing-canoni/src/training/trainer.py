"""
CPU-optimized training loop for cortical column LLMs.
Implements gradient clipping, resource monitoring, and MAE calculation.
"""
import torch
import torch.nn as nn
import psutil
import os
import time
import json
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field, asdict

@dataclass
class TrainingConfig:
    """Configuration for the training loop."""
    num_epochs: int = 10
    batch_size: int = 32
    learning_rate: float = 1e-3
    max_grad_norm: float = 1.0
    seed: int = 42
    device: str = "cpu"
    log_interval: int = 10

@dataclass
class TrainingMetrics:
    """Container for training metrics."""
    epoch: int
    train_loss: float
    train_mae: float
    val_loss: float
    val_mae: float
    elapsed_time: float
    peak_memory_mb: float
    cpu_percent: float

def get_resource_usage() -> Dict[str, float]:
    """
    Monitor CPU and memory usage using psutil.
    Returns a dictionary with current CPU percent and memory usage in MB.
    """
    process = psutil.Process(os.getpid())
    cpu_percent = process.cpu_percent(interval=0.1)
    memory_mb = process.memory_info().rss / (1024 * 1024)
    return {
        "cpu_percent": cpu_percent,
        "memory_mb": memory_mb
    }

def calculate_mae(predictions: torch.Tensor, targets: torch.Tensor) -> float:
    """
    Calculate Mean Absolute Error between predictions and targets.
    Args:
        predictions: Tensor of shape (batch_size, ...)
        targets: Tensor of shape (batch_size, ...)
    Returns:
        float: Mean Absolute Error
    """
    with torch.no_grad():
        mae = torch.mean(torch.abs(predictions - targets))
        return mae.item()

def train_epoch(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    dataloader: torch.utils.data.DataLoader,
    criterion: nn.Module,
    config: TrainingConfig
) -> Tuple[float, float]:
    """
    Train the model for one epoch.
    Args:
        model: The neural network model.
        optimizer: The optimizer.
        dataloader: DataLoader for training data.
        criterion: Loss function.
        config: Training configuration.
    Returns:
        Tuple of (average loss, average MAE) for the epoch.
    """
    model.train()
    total_loss = 0.0
    total_mae = 0.0
    num_batches = 0

    for batch_idx, (data, targets) in enumerate(dataloader):
        data = data.to(config.device)
        targets = targets.to(config.device)

        optimizer.zero_grad()
        outputs = model(data)
        loss = criterion(outputs, targets)
        loss.backward()

        # Gradient clipping by max norm
        torch.nn.utils.clip_grad_norm_(model.parameters(), config.max_grad_norm)

        optimizer.step()

        total_loss += loss.item()
        total_mae += calculate_mae(outputs, targets)
        num_batches += 1

        if batch_idx % config.log_interval == 0:
            resources = get_resource_usage()
            # Log could be extended here, but we keep it minimal for the loop
            pass

    avg_loss = total_loss / num_batches
    avg_mae = total_mae / num_batches
    return avg_loss, avg_mae

def evaluate(
    model: nn.Module,
    dataloader: torch.utils.data.DataLoader,
    criterion: nn.Module,
    config: TrainingConfig
) -> Tuple[float, float]:
    """
    Evaluate the model on a dataset.
    Args:
        model: The neural network model.
        dataloader: DataLoader for evaluation data.
        criterion: Loss function.
        config: Training configuration.
    Returns:
        Tuple of (average loss, average MAE).
    """
    model.eval()
    total_loss = 0.0
    total_mae = 0.0
    num_batches = 0

    with torch.no_grad():
        for data, targets in dataloader:
            data = data.to(config.device)
            targets = targets.to(config.device)

            outputs = model(data)
            loss = criterion(outputs, targets)

            total_loss += loss.item()
            total_mae += calculate_mae(outputs, targets)
            num_batches += 1

    avg_loss = total_loss / num_batches
    avg_mae = total_mae / num_batches
    return avg_loss, avg_mae

def run_training(
    model: nn.Module,
    train_loader: torch.utils.data.DataLoader,
    val_loader: torch.utils.data.DataLoader,
    config: TrainingConfig,
    checkpoint_path: Optional[str] = None
) -> List[TrainingMetrics]:
    """
    Run the full training loop.
    Args:
        model: The neural network model.
        train_loader: DataLoader for training data.
        val_loader: DataLoader for validation data.
        config: Training configuration.
        checkpoint_path: Optional path to save checkpoints.
    Returns:
        List of TrainingMetrics for each epoch.
    """
    device = torch.device(config.device)
    model.to(device)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    criterion = nn.MSELoss()

    metrics_log: List[TrainingMetrics] = []
    start_time = time.time()

    for epoch in range(1, config.num_epochs + 1):
        epoch_start = time.time()
        
        train_loss, train_mae = train_epoch(
            model, optimizer, train_loader, criterion, config
        )
        val_loss, val_mae = evaluate(model, val_loader, criterion, config)
        
        epoch_end = time.time()
        elapsed = epoch_end - epoch_start
        
        resources = get_resource_usage()
        
        metrics = TrainingMetrics(
            epoch=epoch,
            train_loss=train_loss,
            train_mae=train_mae,
            val_loss=val_loss,
            val_mae=val_mae,
            elapsed_time=elapsed,
            peak_memory_mb=resources["memory_mb"],
            cpu_percent=resources["cpu_percent"]
        )
        metrics_log.append(metrics)

        if checkpoint_path:
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "metrics": asdict(metrics)
            }, checkpoint_path)

    total_time = time.time() - start_time
    print(f"Training completed in {total_time:.2f} seconds.")
    
    return metrics_log

def main():
    """
    Entry point for running the trainer.
    This function demonstrates the usage of the training loop with synthetic data.
    """
    import numpy as np
    from torch.utils.data import TensorDataset, DataLoader

    # Set seed for reproducibility
    config = TrainingConfig(seed=42)
    torch.manual_seed(config.seed)
    np.random.seed(config.seed)

    # Generate synthetic data for demonstration
    # Using Lorenz attractor data structure as per benchmarks.py
    n_samples = 1000
    input_dim = 3
    output_dim = 3
    
    X = torch.randn(n_samples, input_dim)
    y = torch.randn(n_samples, output_dim)
    
    # Simple feedforward model for demonstration
    class SimpleModel(nn.Module):
        def __init__(self, input_dim, output_dim):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(input_dim, 64),
                nn.ReLU(),
                nn.Linear(64, output_dim)
            )
        
        def forward(self, x):
            return self.net(x)

    model = SimpleModel(input_dim, output_dim)
    
    train_dataset = TensorDataset(X[:800], y[:800])
    val_dataset = TensorDataset(X[800:], y[800:])
    
    train_loader = DataLoader(train_dataset, batch_size=config.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=config.batch_size)

    # Run training
    metrics = run_training(model, train_loader, val_loader, config)
    
    # Print final metrics
    final = metrics[-1]
    print(f"Final Epoch: {final.epoch}")
    print(f"Train MAE: {final.train_mae:.4f}")
    print(f"Val MAE: {final.val_mae:.4f}")
    print(f"Peak Memory: {final.peak_memory_mb:.2f} MB")

if __name__ == "__main__":
    main()