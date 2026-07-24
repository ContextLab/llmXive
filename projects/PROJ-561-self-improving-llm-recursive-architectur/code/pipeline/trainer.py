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

from config import get_config_summary, PathConfig
from utils.logging import get_log_path, update_cycle_log
from results.trajectory_schema import write_trajectory, TrajectoryEntry

# Global flag for timeout handling
_timeout_triggered = False

def _timeout_handler(signum, frame):
    """Signal handler for timeout."""
    global _timeout_triggered
    _timeout_triggered = True
    raise TimeoutError("Training cycle exceeded allocated time.")

def run_training_cycle_with_timeout(
    model: nn.Module,
    train_loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    cycle_number: int,
    max_timeout_seconds: int = 7200,  # Default 2 hours
    config: Optional[PathConfig] = None
) -> Dict[str, Any]:
    """
    Execute a training cycle with a hard timeout wrapper.
    
    If the cycle exceeds max_timeout_seconds:
    1. Terminates the cycle immediately.
    2. Logs "Timeout" to results/logs/cycle_N.log.
    3. Records partial metrics (up to the point of failure) to results/trajectory.json.
    
    Args:
        model: The model to train.
        train_loader: DataLoader for the training set.
        optimizer: Optimizer instance.
        cycle_number: Current cycle index (used for logging).
        max_timeout_seconds: Maximum allowed duration in seconds.
        config: Path configuration for output files.
    
    Returns:
        A dictionary containing training metrics (partial if timed out).
    """
    global _timeout_triggered
    _timeout_triggered = False
    
    # Determine config if not provided
    if config is None:
        config = PathConfig()
    
    # Set up signal handler (Unix only for SIGALRM)
    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(max_timeout_seconds)
    
    start_time = time.time()
    metrics = {
        "cycle_number": cycle_number,
        "start_time": start_time,
        "status": "running",
        "losses": [],
        "steps_completed": 0,
        "partial": False
    }
    
    try:
        model.train()
        epoch_loss = 0.0
        steps = 0
        
        for batch_idx, batch in enumerate(train_loader):
            if _timeout_triggered:
                break
                
            inputs = batch['input_ids']
            labels = batch['labels']
            
            # Move to device (CPU in this project context)
            inputs = inputs.to('cpu')
            labels = labels.to('cpu')
            
            optimizer.zero_grad()
            outputs = model(inputs, labels=labels)
            loss = outputs.loss
            
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            steps += 1
            metrics["losses"].append(loss.item())
            metrics["steps_completed"] = steps
            
            # Optional: Print progress
            if batch_idx % 10 == 0:
                current_time = time.time()
                elapsed = current_time - start_time
                avg_loss = epoch_loss / steps
                print(f"Cycle {cycle_number}, Step {batch_idx}, Loss: {avg_loss:.4f}, Elapsed: {elapsed:.2f}s")
                
        end_time = time.time()
        metrics["end_time"] = end_time
        metrics["training_time"] = end_time - start_time
        metrics["status"] = "completed"
        metrics["avg_loss"] = epoch_loss / steps if steps > 0 else 0.0
        
    except TimeoutError:
        end_time = time.time()
        metrics["end_time"] = end_time
        metrics["training_time"] = end_time - start_time
        metrics["status"] = "timeout"
        metrics["partial"] = True
        print(f"⚠ Timeout triggered for Cycle {cycle_number} after {metrics['training_time']:.2f}s")
        
    finally:
        # Reset alarm and restore old handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
        
    # 1. Log "Timeout" to results/logs/cycle_N.log if timed out
    if metrics["status"] == "timeout":
        log_path = get_log_path(config, cycle_number)
        update_cycle_log(log_path, {"event": "Timeout", "timestamp": time.time(), "partial_steps": metrics["steps_completed"]})
        print(f"Logged Timeout event to {log_path}")
    
    # 2. Record partial metrics to results/trajectory.json
    # We construct a TrajectoryEntry. Note: If timed out, we may not have all metrics (e.g., eval scores).
    # We record what we have (loss, time, steps) and mark as partial.
    trajectory_entry = {
        "cycle_number": cycle_number,
        "training_time": metrics.get("training_time", 0.0),
        "status": metrics["status"],
        "partial": metrics["partial"],
        "steps_completed": metrics["steps_completed"],
        "avg_loss": metrics.get("avg_loss", None),
        # Placeholder for metrics that might not be available if timed out
        "gsm8k_accuracy": None,
        "arc_accuracy": None,
        "wikitext2_ece": None,
        "param_count": get_model_param_count(model),
        "flops": None, # FLOPs calculation might need to be skipped or partial if timed out
        "timestamp": time.time()
    }
    
    write_trajectory(config, trajectory_entry)
    print(f"Recorded trajectory entry for Cycle {cycle_number} to {config.trajectory_path}")
    
    return metrics

def count_flops(model: nn.Module, input_size: Tuple[int, int]) -> int:
    """
    Estimate FLOPs for a forward pass.
    This is a simplified estimator for GPT-style models.
    """
    # Approximate FLOPs for transformer: 6 * N * d^2 * L (very rough)
    # Or count parameters and multiply by 2 (forward + backward)
    # For this task, we return a placeholder or a simple param-based estimate
    param_count = sum(p.numel() for p in model.parameters())
    # Rough estimate: 2 * params for forward pass
    return 2 * param_count

def train_epoch(
    model: nn.Module,
    train_loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    scheduler: Optional[torch.optim.lr_scheduler._LRScheduler] = None
) -> float:
    """
    Standard training epoch without timeout wrapper.
    The timeout wrapper is now in run_training_cycle_with_timeout.
    """
    model.train()
    epoch_loss = 0.0
    steps = 0
    
    for batch in train_loader:
        inputs = batch['input_ids'].to('cpu')
        labels = batch['labels'].to('cpu')
        
        optimizer.zero_grad()
        outputs = model(inputs, labels=labels)
        loss = outputs.loss
        
        loss.backward()
        optimizer.step()
        
        if scheduler:
            scheduler.step()
        
        epoch_loss += loss.item()
        steps += 1
        
    return epoch_loss / steps if steps > 0 else 0.0

def run_training_cycle(
    cycle_id: str,
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: torch.optim.Optimizer,
    cycle_number: int,
    config: Optional[PathConfig] = None
) -> Dict[str, Any]:
    """
    Wrapper for backward compatibility that calls the timeout-enabled version.
    Uses a default timeout of 2 hours (7200s) as per project constraints.
    """
    return run_training_cycle_with_timeout(
        model=model,
        train_loader=train_loader,
        optimizer=optimizer,
        cycle_number=cycle_number,
        max_timeout_seconds=7200,
        config=config
    )

def get_model_param_count(model: nn.Module) -> int:
    """Helper to count parameters."""
    return sum(p.numel() for p in model.parameters())
