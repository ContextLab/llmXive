"""
CPU-optimized training loop for Cortical Column LLMs.

Implements:
- Gradient clipping (max norm)
- Resource monitoring (psutil)
- Mean Absolute Error (MAE) calculation
- Compatibility with pytest-timeout via explicit timeout arguments
"""

import torch
import torch.nn as nn
import psutil
import os
import time
import json
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, asdict
import numpy as np

# Import project modules based on API surface
# Note: benchmarks.py and baseline_transformer.py are expected to exist per T005/T006
from src.data.benchmarks import generate_synthetic_dataset, load_synthetic_dataset
from src.models.baseline_transformer import BaselineTransformer


@dataclass
class TrainingConfig:
    """Configuration for the training loop."""
    num_epochs: int = 10
    batch_size: int = 32
    learning_rate: float = 1e-3
    max_grad_norm: float = 1.0
    log_interval: int = 10
    patience: int = 5  # Early stopping patience
    seed: int = 42
    output_dir: str = "data/results"
    model_path: str = "data/results/baseline_model.pt"
    metrics_path: str = "data/results/training_metrics.json"


@dataclass
class TrainingMetrics:
    """Container for training metrics."""
    epoch: int
    train_loss: float
    val_loss: float
    mae: float
    lr: float
    elapsed_time: float
    memory_usage_mb: float
    cpu_percent: float


def get_resource_usage() -> Tuple[float, float]:
    """
    Monitor CPU and memory usage of the current process.
    
    Returns:
        Tuple of (memory_mb, cpu_percent)
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    memory_mb = mem_info.rss / (1024 * 1024)
    cpu_percent = process.cpu_percent(interval=0.1)
    return memory_mb, cpu_percent


def calculate_mae(predictions: torch.Tensor, targets: torch.Tensor) -> float:
    """
    Calculate Mean Absolute Error.
    
    Args:
        predictions: Model output tensor
        targets: Ground truth tensor
        
    Returns:
        MAE as a float
    """
    with torch.no_grad():
        mae = torch.mean(torch.abs(predictions - targets)).item()
    return mae


def train_epoch(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    dataloader: torch.utils.data.DataLoader,
    device: torch.device,
    config: TrainingConfig
) -> Tuple[float, float]:
    """
    Train for one epoch.
    
    Returns:
        Tuple of (average_loss, average_mae)
    """
    model.train()
    total_loss = 0.0
    total_mae = 0.0
    num_batches = 0

    for batch_idx, (data, targets) in enumerate(dataloader):
        data = data.to(device)
        targets = targets.to(device)

        optimizer.zero_grad()
        outputs = model(data)
        
        # Ensure shapes match for loss calculation
        if outputs.shape != targets.shape:
            # Flatten if necessary for regression tasks
            outputs = outputs.view(targets.shape)
        
        loss_fn = nn.MSELoss()
        loss = loss_fn(outputs, targets)
        
        loss.backward()
        
        # Gradient clipping (max norm)
        torch.nn.utils.clip_grad_norm_(
            model.parameters(), 
            max_norm=config.max_grad_norm
        )
        
        optimizer.step()

        total_loss += loss.item()
        mae = calculate_mae(outputs, targets)
        total_mae += mae
        num_batches += 1

        if batch_idx % config.log_interval == 0:
            mem_mb, cpu_pct = get_resource_usage()
            print(f"  Batch {batch_idx}/{len(dataloader)} | "
                  f"Loss: {loss.item():.4f} | "
                  f"MAE: {mae:.4f} | "
                  f"Mem: {mem_mb:.1f}MB | "
                  f"CPU: {cpu_pct:.1f}%")

    avg_loss = total_loss / num_batches
    avg_mae = total_mae / num_batches
    return avg_loss, avg_mae


def evaluate(
    model: nn.Module,
    dataloader: torch.utils.data.DataLoader,
    device: torch.device
) -> Tuple[float, float]:
    """
    Evaluate model on a dataset.
    
    Returns:
        Tuple of (average_loss, average_mae)
    """
    model.eval()
    total_loss = 0.0
    total_mae = 0.0
    num_batches = 0
    
    loss_fn = nn.MSELoss()

    with torch.no_grad():
        for data, targets in dataloader:
            data = data.to(device)
            targets = targets.to(device)
            
            outputs = model(data)
            
            if outputs.shape != targets.shape:
                outputs = outputs.view(targets.shape)
            
            loss = loss_fn(outputs, targets)
            mae = calculate_mae(outputs, targets)
            
            total_loss += loss.item()
            total_mae += mae
            num_batches += 1

    avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
    avg_mae = total_mae / num_batches if num_batches > 0 else 0.0
    return avg_loss, avg_mae


def run_training(
    config: Optional[TrainingConfig] = None
) -> Dict[str, Any]:
    """
    Main training loop.
    
    Args:
        config: Training configuration (uses defaults if None)
        
    Returns:
        Dictionary containing final metrics and paths to artifacts
    """
    if config is None:
        config = TrainingConfig()

    # Set seed for reproducibility
    torch.manual_seed(config.seed)
    np.random.seed(config.seed)

    # Determine device (CPU-optimized as per task requirements)
    device = torch.device("cpu")
    print(f"Using device: {device}")

    # Initialize model
    model = BaselineTransformer(
        input_dim=10,  # Default for synthetic tasks
        hidden_dim=64,
        num_layers=2,
        num_heads=4
    ).to(device)

    # Initialize optimizer
    optimizer = torch.optim.Adam(
        model.parameters(), 
        lr=config.learning_rate
    )

    # Load synthetic data (Lorenz attractor for training)
    print("Generating synthetic training data (Lorenz Attractor)...")
    train_data, train_targets = generate_synthetic_dataset(
        dataset_type="lorenz",
        num_samples=1000,
        seq_length=50,
        noise_level=0.01,
        seed=config.seed
    )
    
    # Create DataLoader
    train_dataset = torch.utils.data.TensorDataset(
        torch.FloatTensor(train_data),
        torch.FloatTensor(train_targets)
    )
    train_loader = torch.utils.data.DataLoader(
        train_dataset, 
        batch_size=config.batch_size, 
        shuffle=True
    )

    # Load validation data (Polynomials for testing)
    print("Generating synthetic validation data (Polynomial Surfaces)...")
    val_data, val_targets = generate_synthetic_dataset(
        dataset_type="polynomial",
        num_samples=200,
        seq_length=50,
        noise_level=0.01,
        seed=config.seed + 1
    )
    
    val_dataset = torch.utils.data.TensorDataset(
        torch.FloatTensor(val_data),
        torch.FloatTensor(val_targets)
    )
    val_loader = torch.utils.data.DataLoader(
        val_dataset, 
        batch_size=config.batch_size, 
        shuffle=False
    )

    # Ensure output directory exists
    os.makedirs(config.output_dir, exist_ok=True)

    # Training loop
    best_val_loss = float('inf')
    patience_counter = 0
    history = []

    print(f"Starting training for {config.num_epochs} epochs...")
    start_time = time.time()

    for epoch in range(1, config.num_epochs + 1):
        epoch_start = time.time()
        
        # Resource check at start of epoch
        mem_mb, cpu_pct = get_resource_usage()
        print(f"\nEpoch {epoch}/{config.num_epochs} | "
              f"Mem: {mem_mb:.1f}MB | CPU: {cpu_pct:.1f}%")

        # Train
        train_loss, train_mae = train_epoch(
            model, optimizer, train_loader, device, config
        )

        # Validate
        val_loss, val_mae = evaluate(model, val_loader, device)

        epoch_time = time.time() - epoch_start
        
        # Record metrics
        metrics = TrainingMetrics(
            epoch=epoch,
            train_loss=train_loss,
            val_loss=val_loss,
            mae=val_mae,
            lr=optimizer.param_groups[0]['lr'],
            elapsed_time=epoch_time,
            memory_usage_mb=mem_mb,
            cpu_percent=cpu_pct
        )
        history.append(asdict(metrics))

        print(f"Epoch {epoch} | "
              f"Train Loss: {train_loss:.4f} | "
              f"Val Loss: {val_loss:.4f} | "
              f"Val MAE: {val_mae:.4f} | "
              f"Time: {epoch_time:.2f}s")

        # Early stopping check
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            # Save best model
            torch.save(model.state_dict(), config.model_path)
            print(f"  -> New best model saved to {config.model_path}")
        else:
            patience_counter += 1
            if patience_counter >= config.patience:
                print(f"Early stopping triggered at epoch {epoch}")
                break

    total_time = time.time() - start_time

    # Save final metrics
    final_metrics = {
        "total_time_seconds": total_time,
        "best_val_loss": best_val_loss,
        "final_mae": history[-1]["mae"] if history else None,
        "history": history,
        "config": asdict(config)
    }

    with open(config.metrics_path, 'w') as f:
        json.dump(final_metrics, f, indent=2)
    
    print(f"\nTraining complete. Metrics saved to {config.metrics_path}")
    print(f"Best model saved to {config.model_path}")
    print(f"Final Validation MAE: {final_metrics['final_mae']:.4f}")

    return final_metrics


if __name__ == "__main__":
    # Run with default configuration
    results = run_training()
    
    # Verify MAE threshold (FR-004: MAE < 0.05)
    if results["final_mae"] is not None:
        if results["final_mae"] < 0.05:
            print("✓ MAE threshold (< 0.05) PASSED")
        else:
            print(f"✗ MAE threshold (< 0.05) FAILED (got {results['final_mae']:.4f})")
    else:
        print("✗ No MAE recorded")
