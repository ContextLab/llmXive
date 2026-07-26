"""
CPU-optimized training loop with gradient clipping, resource monitoring, and MAE calculation.
Implements the core training logic for baseline and microcircuit models.
"""
import torch
import torch.nn as nn
import torch.optim as optim
import psutil
import os
import time
import json
import logging
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
    homeostasis_enabled: bool = False
    output_dir: str = "data/logs"


@dataclass
class TrainingMetrics:
    """Accumulated metrics during training."""
    train_losses: List[float] = field(default_factory=list)
    val_losses: List[float] = field(default_factory=list)
    train_maes: List[float] = field(default_factory=list)
    val_maes: List[float] = field(default_factory=list)
    gradient_norms: List[float] = field(default_factory=list)
    resource_usage: List[Dict[str, float]] = field(default_factory=list)
    elapsed_time: float = 0.0
    epochs_completed: int = 0


def get_resource_usage() -> Dict[str, float]:
    """
    Monitor current CPU and memory usage.
    
    Returns:
        Dict with 'cpu_percent', 'memory_percent', 'memory_mb'
    """
    process = psutil.Process(os.getpid())
    cpu_percent = process.cpu_percent(interval=0.1)
    memory_info = process.memory_info()
    
    return {
        "cpu_percent": cpu_percent,
        "memory_percent": process.memory_percent(),
        "memory_mb": memory_info.rss / (1024 * 1024)
    }


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
    optimizer: optim.Optimizer,
    data_loader: torch.utils.data.DataLoader,
    config: TrainingConfig,
    metrics: TrainingMetrics,
    homeostasis_scaler: Optional[Any] = None
) -> float:
    """
    Train the model for one epoch.
    
    Args:
        model: The neural network model
        optimizer: Optimizer instance
        data_loader: DataLoader for training data
        config: Training configuration
        metrics: Object to accumulate metrics
        homeostasis_scaler: Optional homeostatic scaler instance
        
    Returns:
        Average loss for the epoch
    """
    model.train()
    total_loss = 0.0
    num_batches = 0
    
    start_time = time.time()
    
    for batch_idx, (inputs, targets) in enumerate(data_loader):
        inputs = inputs.to(config.device)
        targets = targets.to(config.device)
        
        optimizer.zero_grad()
        
        # Forward pass
        outputs = model(inputs)
        
        # Ensure outputs and targets have compatible shapes for loss
        if outputs.dim() > targets.dim():
            outputs = outputs.squeeze(-1)
        
        # Calculate loss
        loss_fn = nn.MSELoss()
        loss = loss_fn(outputs, targets)
        
        # Backward pass
        loss.backward()
        
        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=config.max_grad_norm)
        
        # Record gradient norm
        grad_norm = torch.norm(
            torch.stack([p.grad.norm() for p in model.parameters() if p.grad is not None])
        ).item()
        metrics.gradient_norms.append(grad_norm)
        
        optimizer.step()
        
        # Apply homeostatic scaling if enabled
        if config.homeostasis_enabled and homeostasis_scaler is not None:
            homeostasis_scaler.step(model)
        
        total_loss += loss.item()
        num_batches += 1
        
        # Log progress
        if batch_idx % config.log_interval == 0:
            current_mae = calculate_mae(outputs, targets)
            resource_usage = get_resource_usage()
            metrics.resource_usage.append(resource_usage)
            
            logger.info(
                f"Epoch batch {batch_idx}/{len(data_loader)} | "
                f"Loss: {loss.item():.6f} | MAE: {current_mae:.6f} | "
                f"Grad Norm: {grad_norm:.6f} | "
                f"RAM: {resource_usage['memory_mb']:.1f}MB"
            )
    
    metrics.elapsed_time += time.time() - start_time
    avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
    metrics.train_losses.append(avg_loss)
    
    return avg_loss


@torch.no_grad()
def evaluate(
    model: nn.Module,
    data_loader: torch.utils.data.DataLoader,
    config: TrainingConfig
) -> Tuple[float, float]:
    """
    Evaluate the model on a dataset.
    
    Args:
        model: The neural network model
        data_loader: DataLoader for evaluation data
        config: Training configuration
        
    Returns:
        Tuple of (average loss, average MAE)
    """
    model.eval()
    total_loss = 0.0
    total_mae = 0.0
    num_batches = 0
    
    for inputs, targets in data_loader:
        inputs = inputs.to(config.device)
        targets = targets.to(config.device)
        
        outputs = model(inputs)
        
        # Ensure outputs and targets have compatible shapes
        if outputs.dim() > targets.dim():
            outputs = outputs.squeeze(-1)
        
        loss_fn = nn.MSELoss()
        loss = loss_fn(outputs, targets)
        mae = calculate_mae(outputs, targets)
        
        total_loss += loss.item()
        total_mae += mae
        num_batches += 1
    
    avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
    avg_mae = total_mae / num_batches if num_batches > 0 else 0.0
    
    metrics = TrainingMetrics()
    metrics.val_losses.append(avg_loss)
    metrics.val_maes.append(avg_mae)
    
    logger.info(f"Evaluation - Loss: {avg_loss:.6f}, MAE: {avg_mae:.6f}")
    
    return avg_loss, avg_mae


def run_training(
    model: nn.Module,
    train_loader: torch.utils.data.DataLoader,
    val_loader: torch.utils.data.DataLoader,
    config: TrainingConfig,
    homeostasis_scaler: Optional[Any] = None
) -> TrainingMetrics:
    """
    Run the full training loop.
    
    Args:
        model: The neural network model to train
        train_loader: DataLoader for training data
        val_loader: DataLoader for validation data
        config: Training configuration
        homeostasis_scaler: Optional homeostatic scaler instance
        
    Returns:
        TrainingMetrics object containing all recorded metrics
    """
    logger.info(f"Starting training on device: {config.device}")
    logger.info(f"Config: epochs={config.num_epochs}, lr={config.learning_rate}, "
               f"batch_size={config.batch_size}, max_grad_norm={config.max_grad_norm}")
    
    # Set random seeds for reproducibility
    torch.manual_seed(config.seed)
    if config.device == "cuda":
        torch.cuda.manual_seed(config.seed)
    
    # Initialize optimizer
    optimizer = optim.Adam(model.parameters(), lr=config.learning_rate)
    
    # Initialize metrics
    metrics = TrainingMetrics()
    
    # Ensure output directory exists
    os.makedirs(config.output_dir, exist_ok=True)
    metrics_file = os.path.join(config.output_dir, "training_metrics.json")
    
    start_time = time.time()
    
    try:
        for epoch in range(config.num_epochs):
            logger.info(f"\n--- Epoch {epoch + 1}/{config.num_epochs} ---")
            
            # Training phase
            train_loss = train_epoch(
                model, optimizer, train_loader, config, metrics, homeostasis_scaler
            )
            
            # Validation phase
            val_loss, val_mae = evaluate(model, val_loader, config)
            
            metrics.epochs_completed = epoch + 1
            
            # Log epoch summary
            logger.info(
                f"Epoch {epoch + 1} completed - "
                f"Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}, "
                f"Val MAE: {val_mae:.6f}"
            )
            
            # Save intermediate metrics
            with open(metrics_file, 'w') as f:
                json.dump(asdict(metrics), f, indent=2)
            
    except KeyboardInterrupt:
        logger.warning("Training interrupted by user")
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise
    
    metrics.elapsed_time = time.time() - start_time
    
    # Final metrics save
    with open(metrics_file, 'w') as f:
        json.dump(asdict(metrics), f, indent=2)
    
    logger.info(f"Training completed in {metrics.elapsed_time:.2f} seconds")
    logger.info(f"Final MAE: {metrics.val_maes[-1]:.6f}")
    
    return metrics