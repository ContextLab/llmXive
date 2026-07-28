import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from typing import Optional, Dict, Any, Tuple
import time
import math
import json
import os
import signal
import sys
from datetime import datetime

from config import get_config, get_trajectory_path
from utils.logging import init_cycle_logger, update_cycle_log
from results.trajectory_schema import write_trajectory, TrajectoryEntry

class TimeoutError(Exception):
    """Custom exception for training timeout."""
    pass

def signal_handler(signum, frame):
    raise TimeoutError("Training cycle exceeded time limit")

def run_training_cycle_with_timeout(
    model: nn.Module,
    train_loader: DataLoader,
    cycle_number: int,
    timeout_seconds: Optional[int] = 3600,  # Default 1 hour
    optimizer: Optional[torch.optim.Optimizer] = None,
    max_epochs: int = 1
) -> Dict[str, Any]:
    """
    Execute a training cycle with a hard timeout.
    
    If timeout is exceeded:
    1. Logs "Timeout" to results/logs/cycle_N.log
    2. Records partial metrics to results/trajectory.json
    3. Raises TimeoutError to be handled by the main loop.
    """
    config = get_config()
    log_path = os.path.join(config.results_dir, "logs", f"cycle_{cycle_number}.log")
    trajectory_path = get_trajectory_path()
    
    # Ensure log directory exists
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    # Initialize logger for this cycle
    logger = init_cycle_logger(log_path, cycle_number)
    logger.info(f"Starting training cycle {cycle_number} with timeout {timeout_seconds}s")
    
    start_time = time.time()
    partial_metrics = {
        "cycle": cycle_number,
        "status": "timeout",
        "start_time": datetime.now().isoformat(),
        "partial_training_time": 0.0,
        "metrics": {}
    }
    
    # Set up timeout signal handler
    old_handler = signal.signal(signal.SIGALRM, signal_handler)
    if timeout_seconds:
        signal.alarm(timeout_seconds)
    
    try:
        # Run the actual training loop
        epoch_metrics = run_epoch_with_timeout_logic(
            model, train_loader, optimizer, max_epochs, logger
        )
        
        # If we get here, training completed successfully within timeout
        signal.alarm(0)  # Cancel alarm
        end_time = time.time()
        training_time = end_time - start_time
        
        partial_metrics["status"] = "completed"
        partial_metrics["partial_training_time"] = training_time
        partial_metrics["metrics"] = epoch_metrics
        
        logger.info(f"Cycle {cycle_number} completed successfully in {training_time:.2f}s")
        
        return partial_metrics
        
    except TimeoutError:
        signal.alarm(0)  # Cancel alarm
        end_time = time.time()
        elapsed = end_time - start_time
        
        partial_metrics["partial_training_time"] = elapsed
        partial_metrics["status"] = "timeout"
        
        # Log the timeout event
        logger.error(f"TIMEOUT: Cycle {cycle_number} exceeded {timeout_seconds}s limit after {elapsed:.2f}s")
        
        # Record partial metrics to trajectory (even if incomplete)
        try:
            trajectory_entry = TrajectoryEntry(
                cycle_number=cycle_number,
                param_count=0,  # Could be calculated if needed
                gsm8k_accuracy=None,
                arc_accuracy=None,
                wikitext2_ece=None,
                flops=0,
                training_time=elapsed,
                status="timeout",
                timestamp=datetime.now().isoformat()
            )
            write_trajectory(trajectory_entry, trajectory_path)
            logger.info(f"Recorded partial trajectory for cycle {cycle_number}")
        except Exception as e:
            logger.error(f"Failed to write partial trajectory: {e}")
        
        raise
        
    finally:
        # Restore old signal handler
        signal.signal(signal.SIGALRM, old_handler)

def run_epoch_with_timeout_logic(
    model: nn.Module,
    train_loader: DataLoader,
    optimizer: Optional[torch.optim.Optimizer],
    max_epochs: int,
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Core training loop logic.
    Note: Timeout is handled by the wrapper via signal, not inside this loop.
    """
    if optimizer is None:
        from config import get_config
        cfg = get_config()
        optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.learning_rate)
        
    model.train()
    total_loss = 0.0
    num_batches = 0
    
    for epoch in range(max_epochs):
        logger.info(f"Starting epoch {epoch + 1}/{max_epochs}")
        for batch_idx, batch in enumerate(train_loader):
            # In a real implementation, we would unpack batch here
            # For this timeout task, we assume batch is a dict or tuple with input/target
            if isinstance(batch, dict):
                inputs = batch.get("input_ids")
                targets = batch.get("labels")
            else:
                inputs, targets = batch[0], batch[1]
            
            if inputs is None or targets is None:
                continue
                
            optimizer.zero_grad()
            
            # Forward pass
            outputs = model(inputs)
            loss = torch.nn.functional.cross_entropy(
                outputs.logits.view(-1, outputs.logits.size(-1)),
                targets.view(-1)
            )
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
            
            # Log progress
            if batch_idx % 10 == 0:
                logger.debug(f"Epoch {epoch+1}, Batch {batch_idx}, Loss: {loss.item():.4f}")
                
    avg_loss = total_loss / max(num_batches, 1)
    return {"loss": avg_loss, "batches": num_batches}

def count_flops(model: nn.Module, input_shape: Tuple[int, ...]) -> int:
    """
    Estimate FLOPs for a forward pass.
    Simplified estimation based on parameter count and input size.
    """
    # Simple estimation: 2 * params * input_tokens (approx for dense layers)
    param_count = sum(p.numel() for p in model.parameters())
    input_tokens = input_shape[1] if len(input_shape) > 1 else input_shape[0]
    return 2 * param_count * input_tokens

def train_epoch(
    model: nn.Module,
    train_loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    epoch: int
) -> float:
    """
    Train a single epoch.
    Deprecated in favor of run_training_cycle_with_timeout, but kept for API compatibility.
    """
    model.train()
    total_loss = 0.0
    num_batches = 0
    
    for batch in train_loader:
        if isinstance(batch, dict):
            inputs = batch.get("input_ids")
            targets = batch.get("labels")
        else:
            inputs, targets = batch[0], batch[1]
            
        if inputs is None or targets is None:
            continue
        
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = torch.nn.functional.cross_entropy(
            outputs.logits.view(-1, outputs.logits.size(-1)),
            targets.view(-1)
        )
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        num_batches += 1
        
    return total_loss / max(num_batches, 1)

def run_training_cycle(
    model: nn.Module,
    train_loader: DataLoader,
    cycle_number: int,
    timeout_seconds: Optional[int] = 3600
) -> Dict[str, Any]:
    """
    Wrapper for run_training_cycle_with_timeout for backward compatibility.
    """
    return run_training_cycle_with_timeout(
        model, train_loader, cycle_number, timeout_seconds
    )

def get_model_param_count(model: nn.Module) -> int:
    """Helper to get parameter count."""
    return sum(p.numel() for p in model.parameters())