import torch
import torch.nn as nn
import torch.optim as optim
import psutil
import os
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple
import json
import logging

from src.training.homeostasis import log_gradient_norms, HomeostaticScaler, apply_scaling_hook

@dataclass
class TrainingConfig:
    """Configuration for training."""
    num_epochs: int = 10
    batch_size: int = 32
    learning_rate: float = 0.001
    gradient_clip_norm: float = 1.0
    device: str = "cpu"
    seed: int = 42

@dataclass
class TrainingMetrics:
    """Metrics from training."""
    train_loss: float = 0.0
    test_loss: float = 0.0
    train_mae: float = 0.0
    test_mae: float = 0.0
    epoch_times: List[float] = None
    gradient_norms: List[float] = None

    def __post_init__(self):
        if self.epoch_times is None:
            self.epoch_times = []
        if self.gradient_norms is None:
            self.gradient_norms = []

def get_resource_usage() -> Dict[str, float]:
    """Get current resource usage."""
    process = psutil.Process(os.getpid())
    return {
        "memory_mb": process.memory_info().rss / 1024 / 1024,
        "cpu_percent": psutil.cpu_percent(interval=0.1)
    }

def calculate_mae(model: nn.Module, X: torch.Tensor, y: torch.Tensor) -> float:
    """Calculate Mean Absolute Error."""
    model.eval()
    with torch.no_grad():
        predictions = model(X)
        mae = torch.mean(torch.abs(predictions - y)).item()
    return mae

def train_epoch(
    model: nn.Module,
    optimizer: optim.Optimizer,
    train_loader: torch.utils.data.DataLoader,
    config: TrainingConfig,
    gradient_log_path: Optional[str] = None,
    step_counter: Optional[int] = None,
    homeostatic_scaler: Optional[HomeostaticScaler] = None
) -> Tuple[float, List[float]]:
    """Train one epoch."""
    model.train()
    total_loss = 0.0
    gradient_norms = []
    step = 0 if step_counter is None else step_counter

    for batch_idx, (data, target) in enumerate(train_loader):
        data, target = data.to(config.device), target.to(config.device)

        optimizer.zero_grad()
        output = model(data)
        loss = nn.functional.mse_loss(output, target)
        loss.backward()

        # Log gradient norms if path provided
        if gradient_log_path is not None and step_counter is not None:
            norms = log_gradient_norms(model, step_counter)
            gradient_norms.extend(norms)
            step_counter += 1

        # Apply gradient clipping
        torch.nn.utils.clip_grad_norm_(model.parameters(), config.gradient_clip_norm)

        # Apply homeostatic scaling if enabled
        if homeostatic_scaler is not None:
            apply_scaling_hook(optimizer, step_counter)
            step_counter += 1

        optimizer.step()
        total_loss += loss.item()

    return total_loss / len(train_loader), gradient_norms

def evaluate(
    model: nn.Module,
    test_loader: torch.utils.data.DataLoader,
    config: TrainingConfig
) -> float:
    """Evaluate model on test set."""
    model.eval()
    total_loss = 0.0
    with torch.no_grad():
        for data, target in test_loader:
            data, target = data.to(config.device), target.to(config.device)
            output = model(data)
            loss = nn.functional.mse_loss(output, target)
            total_loss += loss.item()
    return total_loss / len(test_loader)

def run_training(
    model: nn.Module,
    optimizer: optim.Optimizer,
    train_loader: torch.utils.data.DataLoader,
    test_loader: torch.utils.data.DataLoader,
    config: TrainingConfig,
    gradient_log_path: Optional[str] = None,
    use_homeostasis: bool = False,
    target_ei_ratio: float = 4.0
) -> TrainingMetrics:
    """Run full training loop with optional gradient logging and homeostasis."""
    logger = logging.getLogger(__name__)
    logger.info(f"Starting training for {config.num_epochs} epochs")

    all_gradient_norms = []
    epoch_times = []
    step_counter = 0

    # Setup homeostatic scaler if enabled
    homeostatic_scaler = None
    if use_homeostasis:
        homeostatic_scaler = HomeostaticScaler(target_ei_ratio=target_ei_ratio)
        logger.info(f"Homeostasis enabled with target E/I ratio: {target_ei_ratio}")

    for epoch in range(config.num_epochs):
        epoch_start = time.time()
        logger.info(f"Epoch {epoch + 1}/{config.num_epochs}")

        # Train one epoch
        train_loss, epoch_gradient_norms = train_epoch(
            model=model,
            optimizer=optimizer,
            train_loader=train_loader,
            config=config,
            gradient_log_path=gradient_log_path,
            step_counter=step_counter,
            homeostatic_scaler=homeostatic_scaler
        )

        # Update step counter
        if gradient_log_path is not None:
            step_counter += len(train_loader)
        if use_homeostasis:
            step_counter += len(train_loader)

        all_gradient_norms.extend(epoch_gradient_norms)

        # Evaluate
        test_loss = evaluate(model, test_loader, config)
        train_mae = calculate_mae(model, train_loader.dataset.tensors[0], train_loader.dataset.tensors[1])
        test_mae = calculate_mae(model, test_loader.dataset.tensors[0], test_loader.dataset.tensors[1])

        epoch_time = time.time() - epoch_start
        epoch_times.append(epoch_time)

        # Get resource usage
        resources = get_resource_usage()
        logger.info(
            f"Epoch {epoch + 1}: Train Loss={train_loss:.4f}, "
            f"Test Loss={test_loss:.4f}, MAE (train/test)={train_mae:.4f}/{test_mae:.4f}, "
            f"Time={epoch_time:.2f}s, Memory={resources['memory_mb']:.1f}MB"
        )

    # Final evaluation
    final_train_mae = calculate_mae(model, train_loader.dataset.tensors[0], train_loader.dataset.tensors[1])
    final_test_mae = calculate_mae(model, test_loader.dataset.tensors[0], test_loader.dataset.tensors[1])

    metrics = TrainingMetrics(
        train_loss=train_loss,
        test_loss=test_loss,
        train_mae=final_train_mae,
        test_mae=final_test_mae,
        epoch_times=epoch_times,
        gradient_norms=all_gradient_norms
    )

    logger.info(f"Training completed. Final MAE: {final_train_mae:.4f}/{final_test_mae:.4f}")
    return metrics
