import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from typing import Optional, Dict, Any, Tuple
import time
import math
import signal
import os
import sys
import json
import logging
from datetime import datetime

from config import get_config
from utils.logging import init_cycle_logger, update_cycle_log, get_log_path
from results.trajectory_schema import write_trajectory, TrajectoryEntry

class TimeoutError(Exception):
    """Custom exception raised when a training cycle exceeds the time limit."""
    pass

def signal_handler(signum, frame):
    """Signal handler to raise TimeoutError when SIGALRM is received."""
    raise TimeoutError("Training cycle exceeded time limit")

def run_training_cycle_with_timeout(
    cycle_number: int,
    model: nn.Module,
    train_loader: DataLoader,
    timeout_seconds: int,
    logger_name: str = "cycle_trainer"
) -> Dict[str, Any]:
    """
    Run a training cycle with a hard timeout enforcement.
    
    If the cycle exceeds `timeout_seconds`, it terminates the process,
    logs "Timeout" to the cycle log, and records partial metrics to 
    results/trajectory.json.
    
    Args:
        cycle_number: The current cycle index.
        model: The model to train.
        train_loader: DataLoader for the training data.
        timeout_seconds: Maximum allowed duration for the cycle.
        logger_name: Name prefix for the logger.
    
    Returns:
        A dictionary containing cycle metrics (partial or complete).
    
    Raises:
        TimeoutError: If the cycle exceeds the time limit.
        SystemExit: If the process is terminated due to timeout.
    """
    config = get_config()
    
    # Initialize logger for this specific cycle
    log_path = get_log_path(cycle_number)
    logger = init_cycle_logger(log_path, logger_name)
    
    metrics = {
        "cycle_number": cycle_number,
        "status": "in_progress",
        "start_time": time.time(),
        "end_time": None,
        "timeout_occurred": False,
        "partial_metrics": {}
    }
    
    def timeout_callback(signum, frame):
        # Log timeout event
        logger.error("Timeout: Training cycle exceeded time limit.")
        metrics["status"] = "timeout"
        metrics["end_time"] = time.time()
        metrics["timeout_occurred"] = True
        metrics["partial_metrics"] = {
            "duration": metrics["end_time"] - metrics["start_time"],
            "timestamp": datetime.now().isoformat()
        }
        
        # Record partial metrics to trajectory.json
        # We create a partial entry since the cycle didn't finish
        try:
            partial_entry = TrajectoryEntry(
                cycle_number=cycle_number,
                param_count=get_model_param_count(model),
                GSM8K=None,
                ARC=None,
                ECE=None,
                FLOPs=0,
                training_time=metrics["duration"],
                status="timeout",
                timestamp=datetime.now().isoformat()
            )
            write_trajectory([partial_entry])
        except Exception as e:
            logger.error(f"Failed to write partial trajectory: {e}")
        
        # Force exit to terminate the process
        sys.exit(1)
    
    # Set up the alarm signal
    signal.signal(signal.SIGALRM, timeout_callback)
    signal.alarm(timeout_seconds)
    
    try:
        logger.info(f"Starting training cycle {cycle_number} with timeout {timeout_seconds}s")
        
        # Run the actual training loop
        epoch_metrics = run_epoch_with_timeout_logic(
            model, train_loader, logger
        )
        
        # Cancel the alarm if training completes successfully
        signal.alarm(0)
        
        metrics["status"] = "completed"
        metrics["end_time"] = time.time()
        metrics["duration"] = metrics["end_time"] - metrics["start_time"]
        metrics.update(epoch_metrics)
        
        logger.info(f"Cycle {cycle_number} completed successfully in {metrics['duration']:.2f}s")
        
        return metrics
        
    except TimeoutError:
        # This shouldn't be reached because signal_handler calls sys.exit
        # but we handle it just in case
        signal.alarm(0)
        raise

def run_epoch_with_timeout_logic(
    model: nn.Module,
    train_loader: DataLoader,
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Execute a single training epoch with standard logic.
    This is the core training loop that runs under the timeout watch.
    """
    device = torch.device("cpu")  # CPU-only as per constraints
    model.to(device)
    model.train()
    
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=get_config().learning_rate)
    
    total_loss = 0.0
    num_batches = 0
    start_time = time.time()
    
    for batch_idx, (inputs, targets) in enumerate(train_loader):
        inputs, targets = inputs.to(device), targets.to(device)
        
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        num_batches += 1
        
        # Log progress
        if batch_idx % 10 == 0:
            elapsed = time.time() - start_time
            logger.debug(f"Batch {batch_idx}/{len(train_loader)}, Loss: {loss.item():.4f}, Elapsed: {elapsed:.2f}s")
    
    avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
    epoch_time = time.time() - start_time
    
    # Count FLOPs (simplified estimation)
    flops = count_flops(model, train_loader)
    
    return {
        "loss": avg_loss,
        "training_time": epoch_time,
        "flops": flops,
        "batches_processed": num_batches
    }

def count_flops(model: nn.Module, train_loader: DataLoader) -> int:
    """
    Estimate FLOPs for the model based on its architecture and input size.
    This is a simplified estimation for CPU-based training.
    """
    # Simplified FLOP count: 2 * num_params * batch_size * sequence_length
    # This is a rough approximation for GPT-like models
    num_params = get_model_param_count(model)
    
    # Get a sample batch to estimate sequence length and batch size
    try:
        sample_inputs, _ = next(iter(train_loader))
        batch_size = sample_inputs.shape[0]
        seq_len = sample_inputs.shape[1] if len(sample_inputs.shape) > 1 else 1
    except StopIteration:
        batch_size = 4
        seq_len = 128
    
    # Rough FLOP estimate for forward + backward pass
    flops = 2 * num_params * batch_size * seq_len * 2  # Forward + Backward
    return int(flops)

def get_model_param_count(model: nn.Module) -> int:
    """Return the total number of parameters in the model."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

def train_epoch(
    model: nn.Module,
    train_loader: DataLoader,
    epoch: int,
    logger: logging.Logger
) -> float:
    """
    Legacy wrapper for train_epoch that runs without explicit timeout logic.
    The timeout logic is now encapsulated in run_training_cycle_with_timeout.
    """
    device = torch.device("cpu")
    model.to(device)
    model.train()
    
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=get_config().learning_rate)
    
    total_loss = 0.0
    
    for inputs, targets in train_loader:
        inputs, targets = inputs.to(device), targets.to(device)
        
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
    
    avg_loss = total_loss / len(train_loader)
    logger.info(f"Epoch {epoch} completed with average loss: {avg_loss:.4f}")
    return avg_loss

def run_training_cycle(
    cycle_number: int,
    model: nn.Module,
    train_loader: DataLoader,
    timeout_seconds: int
) -> Dict[str, Any]:
    """
    Main entry point for running a training cycle with timeout enforcement.
    This function wraps the timeout logic and training execution.
    """
    return run_training_cycle_with_timeout(
        cycle_number, model, train_loader, timeout_seconds
    )