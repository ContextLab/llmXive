import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from typing import Optional, Dict, Any, Tuple
import time
import math
import os
import json
import signal
import sys

from config import get_config, get_trajectory_path, get_ram_limit
from results.trajectory_schema import write_trajectory, TrajectoryEntry
from utils.logging import init_cycle_logger, update_cycle_log, get_log_path
from pipeline.memory import get_memory_usage_gb

# Global flag for timeout termination
_timeout_triggered = False

def _timeout_handler(signum, frame):
    """Signal handler for timeout termination."""
    global _timeout_triggered
    _timeout_triggered = True
    raise TimeoutError("Training cycle exceeded timeout limit.")

def run_training_cycle_with_timeout(
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: torch.optim.Optimizer,
    cycle_number: int,
    timeout_seconds: int = 3600,
    max_epochs: int = 1
) -> Tuple[Dict[str, float], bool]:
    """
    Run a training cycle with a hard timeout wrapper.
    
    If the cycle exceeds timeout_seconds, it terminates gracefully,
    logs "Timeout" to results/logs/cycle_N.log, and records partial metrics
    to results/trajectory.json.
    
    Args:
        model: The model to train.
        dataloader: DataLoader for the training dataset.
        optimizer: Optimizer instance.
        cycle_number: Current cycle index (used for logging).
        timeout_seconds: Maximum allowed time in seconds.
        max_epochs: Maximum epochs to run if no timeout occurs.
        
    Returns:
        Tuple of (metrics_dict, timed_out_flag)
    """
    global _timeout_triggered
    _timeout_triggered = False
    
    config = get_config()
    log_path = get_log_path(cycle_number)
    trajectory_path = get_trajectory_path()
    
    # Initialize logger for this cycle
    logger = init_cycle_logger(cycle_number)
    
    start_time = time.time()
    metrics = {
        "cycle": cycle_number,
        "start_time": start_time,
        "training_loss": 0.0,
        "param_count": 0,
        "flops": 0,
        "status": "running"
    }
    
    try:
        # Set up signal handler for timeout
        # Note: signal.SIGALRM is only available on Unix systems
        if hasattr(signal, 'SIGALRM'):
            signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(timeout_seconds)
        
        logger.info(f"Starting training cycle {cycle_number} with timeout {timeout_seconds}s")
        
        total_loss = 0.0
        total_steps = 0
        epoch = 0
        
        for epoch in range(max_epochs):
            if _timeout_triggered:
                raise TimeoutError("Timeout triggered during epoch")
            
            model.train()
            epoch_loss = 0.0
            batch_count = 0
            
            for batch_idx, batch in enumerate(dataloader):
                if _timeout_triggered:
                    raise TimeoutError("Timeout triggered during batch")
                
                # Check time periodically
                elapsed = time.time() - start_time
                if elapsed > timeout_seconds:
                    raise TimeoutError("Timeout exceeded")
                
                inputs = batch['input_ids']
                labels = batch['labels']
                
                if hasattr(inputs, 'device'):
                    inputs = inputs.to(next(model.parameters()).device)
                if hasattr(labels, 'device'):
                    labels = labels.to(next(model.parameters()).device)
                
                optimizer.zero_grad()
                outputs = model(inputs, labels=labels)
                loss = outputs.loss
                
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
                batch_count += 1
                total_steps += 1
                
                # Log progress
                if batch_idx % 10 == 0:
                    current_ram = get_memory_usage_gb()
                    logger.debug(f"Cycle {cycle_number}, Epoch {epoch}, Batch {batch_idx}, Loss: {loss.item():.4f}, RAM: {current_ram:.2f}GB")
            
            avg_epoch_loss = epoch_loss / max(batch_count, 1)
            total_loss += avg_epoch_loss
            logger.info(f"Epoch {epoch} complete. Average Loss: {avg_epoch_loss:.4f}")
            
        final_loss = total_loss / max(max_epochs, 1)
        metrics["training_loss"] = final_loss
        metrics["param_count"] = sum(p.numel() for p in model.parameters())
        metrics["status"] = "completed"
        metrics["end_time"] = time.time()
        metrics["duration"] = metrics["end_time"] - metrics["start_time"]
        
        logger.info(f"Cycle {cycle_number} completed successfully in {metrics['duration']:.2f}s")
        
    except TimeoutError as e:
        logger.error(f"Cycle {cycle_number} TIMED OUT: {str(e)}")
        metrics["status"] = "timeout"
        metrics["end_time"] = time.time()
        metrics["duration"] = metrics["end_time"] - metrics["start_time"]
        metrics["training_loss"] = total_loss / max(epoch + 1, 1) if epoch >= 0 else 0.0
        
        # Write timeout log
        with open(log_path, 'a') as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Timeout: {str(e)}\n")
            f.write(f"Cycle {cycle_number} terminated after {metrics['duration']:.2f}s\n")
            f.write(f"Partial metrics recorded to trajectory\n")
        
        # Record partial metrics to trajectory
        partial_entry = TrajectoryEntry(
            cycle_number=cycle_number,
            param_count=metrics["param_count"],
            gsm8k_accuracy=None,  # Not computed due to timeout
            arc_accuracy=None,
            wikitext2_ece=None,
            flops=0,  # Not computed
            training_time=metrics["duration"],
            status="timeout",
            timestamp=metrics["end_time"]
        )
        write_trajectory(partial_entry)
        
        return metrics, True
        
    finally:
        # Cancel alarm if set
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)
        
    return metrics, False

def count_flops(model: nn.Module, input_shape: Tuple[int, int]) -> int:
    """
    Estimate FLOPs for a forward pass of the model.
    Note: This is a simplified estimator.
    
    Args:
        model: The model to count FLOPs for.
        input_shape: Shape of input tensor (batch_size, seq_len).
        
    Returns:
        Estimated FLOP count.
    """
    # Simplified FLOP estimation based on parameter count and input size
    # For a transformer, FLOPs ≈ 6 * params * sequence_length (rough approximation)
    param_count = sum(p.numel() for p in model.parameters())
    batch_size, seq_len = input_shape
    flops = 6 * param_count * seq_len * batch_size
    return flops

def train_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: torch.optim.Optimizer,
    epoch: int
) -> float:
    """
    Train one epoch of the model.
    
    Args:
        model: The model to train.
        dataloader: DataLoader for the training dataset.
        optimizer: Optimizer instance.
        epoch: Current epoch number.
        
    Returns:
        Average loss for the epoch.
    """
    model.train()
    total_loss = 0.0
    batch_count = 0
    
    for batch_idx, batch in enumerate(dataloader):
        inputs = batch['input_ids']
        labels = batch['labels']
        
        if hasattr(inputs, 'device'):
            inputs = inputs.to(next(model.parameters()).device)
        if hasattr(labels, 'device'):
            labels = labels.to(next(model.parameters()).device)
        
        optimizer.zero_grad()
        outputs = model(inputs, labels=labels)
        loss = outputs.loss
        
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        batch_count += 1
    
    return total_loss / max(batch_count, 1)

def run_training_cycle(
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: torch.optim.Optimizer,
    cycle_number: int,
    max_epochs: int = 1
) -> Dict[str, float]:
    """
    Run a full training cycle without timeout enforcement.
    Used for internal calls where timeout is handled externally.
    
    Args:
        model: The model to train.
        dataloader: DataLoader for the training dataset.
        optimizer: Optimizer instance.
        cycle_number: Current cycle index.
        max_epochs: Number of epochs to run.
        
    Returns:
        Dictionary of metrics.
    """
    total_loss = 0.0
    for epoch in range(max_epochs):
        epoch_loss = train_epoch(model, dataloader, optimizer, epoch)
        total_loss += epoch_loss
    
    metrics = {
        "cycle": cycle_number,
        "training_loss": total_loss / max(max_epochs, 1),
        "param_count": sum(p.numel() for p in model.parameters()),
        "status": "completed"
    }
    return metrics

def get_model_param_count(model: nn.Module) -> int:
    """
    Get the total number of parameters in a model.
    
    Args:
        model: The model to count parameters for.
        
    Returns:
        Total parameter count.
    """
    return sum(p.numel() for p in model.parameters())
