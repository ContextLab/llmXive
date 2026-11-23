import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from typing import Optional, Dict, Any, Tuple
import time
import math
import signal
import os
import json
import logging
from datetime import datetime

from config import get_config
from results.trajectory_schema import write_trajectory, TrajectoryEntry
from utils.logging import log_warning, log_error, get_logger

class TimeoutError(Exception):
    """Custom timeout exception for training cycles."""
    pass

def signal_handler(signum, frame):
    """Signal handler for timeout enforcement."""
    raise TimeoutError("Training cycle exceeded time limit")

def run_training_cycle_with_timeout(
    model: nn.Module,
    train_loader: DataLoader,
    cycle_number: int,
    timeout_seconds: int = 3600,
    modification_proposal: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run a training cycle with a hard timeout.
    
    If the cycle exceeds timeout_seconds, it terminates, logs "Timeout" to
    results/logs/cycle_N.log, and records partial metrics to results/trajectory.json.
    
    Args:
        model: The model to train.
        train_loader: DataLoader for training data.
        cycle_number: Current cycle number (used for logging).
        timeout_seconds: Maximum allowed time for the cycle.
        modification_proposal: Optional proposal dict to include in partial metrics.
    
    Returns:
        Dict containing metrics (partial if timeout occurred).
    """
    config = get_config()
    logger = get_logger()
    metrics = {
        "cycle_number": cycle_number,
        "status": "running",
        "start_time": time.time(),
        "training_loss": None,
        "params": 0,
        "flops": 0,
        "duration": 0.0
    }

    # Set up signal handler for timeout
    old_handler = signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(timeout_seconds)

    try:
        logger.info(f"Starting cycle {cycle_number} with timeout {timeout_seconds}s")
        
        # Run training
        loss, flops = train_epoch(model, train_loader)
        
        # Cancel alarm
        signal.alarm(0)
        
        metrics["status"] = "completed"
        metrics["training_loss"] = loss
        metrics["flops"] = flops
        metrics["params"] = get_model_param_count(model)
        metrics["duration"] = time.time() - metrics["start_time"]
        
        logger.info(f"Cycle {cycle_number} completed successfully")
        
    except TimeoutError as e:
        signal.alarm(0)  # Cancel alarm
        
        # Log timeout to cycle log
        log_timeout_event(cycle_number, e, metrics)
        
        # Record partial metrics
        metrics["status"] = "timeout"
        metrics["duration"] = time.time() - metrics["start_time"]
        metrics["error"] = str(e)
        
        # Write partial trajectory entry
        write_timeout_trajectory(cycle_number, metrics, modification_proposal)
        
        logger.error(f"Cycle {cycle_number} timed out after {metrics['duration']:.2f}s")
        raise
        
    finally:
        # Restore old signal handler
        signal.signal(signal.SIGALRM, old_handler)
        
    return metrics

def log_timeout_event(cycle_number: int, exception: Exception, partial_metrics: Dict[str, Any]):
    """Log timeout event to results/logs/cycle_N.log."""
    from config import get_config
    import os
    
    config = get_config()
    log_dir = os.path.join(config.paths.results_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_path = os.path.join(log_dir, f"cycle_{cycle_number}.log")
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "event": "Timeout",
        "exception": str(exception),
        "partial_metrics": partial_metrics
    }
    
    # Append to log file
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")

def write_timeout_trajectory(cycle_number: int, metrics: Dict[str, Any], modification_proposal: Optional[Dict[str, Any]]):
    """Write partial metrics to results/trajectory.json for timeout case."""
    from config import get_config
    
    config = get_config()
    
    # Create a partial trajectory entry
    entry = TrajectoryEntry(
        cycle_number=cycle_number,
        param_count=metrics.get("params", 0),
        GSM8K_accuracy=0.0,  # Not evaluated due to timeout
        ARC_Challenge_accuracy=0.0,
        BoolQ_ECE=0.0,
        FLOPs=metrics.get("flops", 0),
        training_time=metrics.get("duration", 0.0),
        slope=0.0,
        intercept=0.0,
        r_squared=0.0,
        trend_direction="timeout",
        status="timeout",
        modification_type=modification_proposal.get("modification_type", "unknown") if modification_proposal else None,
        modification_magnitude=modification_proposal.get("magnitude", 0) if modification_proposal else None
    )
    
    write_trajectory(entry)

def run_epoch_with_timeout_logic(
    model: nn.Module,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    timeout_seconds: int
) -> Tuple[float, int]:
    """
    Run a single epoch with timeout logic.
    
    Args:
        model: Model to train.
        loader: DataLoader.
        optimizer: Optimizer.
        timeout_seconds: Timeout for this epoch.
    
    Returns:
        Tuple of (loss, flops)
    """
    start = time.time()
    signal.alarm(timeout_seconds)
    
    try:
        model.train()
        total_loss = 0.0
        num_batches = 0
        
        for batch in loader:
            # Check timeout periodically
            if time.time() - start > timeout_seconds:
                raise TimeoutError("Epoch exceeded timeout")
            
            # Simplified training step (actual implementation would use real data)
            # This is a placeholder for the actual training logic
            num_batches += 1
            
        signal.alarm(0)
        return total_loss / max(num_batches, 1), 0
        
    except TimeoutError:
        signal.alarm(0)
        raise

def count_flops(model: nn.Module, input_shape: Tuple[int, ...]) -> int:
    """
    Count FLOPs for a model.
    
    Args:
        model: The model.
        input_shape: Shape of input tensor.
    
    Returns:
        Estimated FLOP count.
    """
    # Simplified FLOP counting - in production, use torch.profiler
    total_flops = 0
    for param in model.parameters():
        # Rough estimate: 2 * num_params for forward pass
        total_flops += 2 * param.numel()
    return total_flops

def get_model_param_count(model: nn.Module) -> int:
    """Get total parameter count of a model."""
    return sum(p.numel() for p in model.parameters())

def train_epoch(model: nn.Module, train_loader: DataLoader) -> Tuple[float, int]:
    """
    Train one epoch on the given dataset.
    
    Args:
        model: Model to train.
        train_loader: DataLoader for training data.
    
    Returns:
        Tuple of (average_loss, total_flops)
    """
    config = get_config()
    model.train()
    
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config.hyperparameters.learning_rate,
        weight_decay=0.01
    )
    
    criterion = nn.CrossEntropyLoss()
    
    total_loss = 0.0
    total_flops = 0
    num_batches = 0
    
    for batch_idx, batch in enumerate(train_loader):
        # Simplified batch processing
        # In real implementation, this would handle actual data loading
        inputs = batch.get("input_ids", torch.randint(0, 1000, (config.hyperparameters.batch_size, 10)))
        labels = batch.get("labels", torch.randint(0, 1000, (config.hyperparameters.batch_size, 10)))
        
        optimizer.zero_grad()
        
        # Forward pass
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        num_batches += 1
        
        # Estimate FLOPs (simplified)
        total_flops += count_flops(model, inputs.shape)
        
        # Memory monitoring
        from pipeline.memory import get_memory_usage_gb
        current_ram = get_memory_usage_gb()
        if current_ram > config.safety_constraints.ram_limit_gb:
            from pipeline.memory import enforce_ram_limit
            enforce_ram_limit(current_ram, config.safety_constraints.ram_limit_gb)
    
    avg_loss = total_loss / max(num_batches, 1)
    return avg_loss, total_flops

def run_training_cycle(
    model: nn.Module,
    train_loader: DataLoader,
    cycle_number: int,
    timeout_seconds: int = 3600,
    modification_proposal: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Main entry point for a training cycle with timeout enforcement.
    
    This wraps the timeout logic around the training process.
    
    Args:
        model: Model to train.
        train_loader: DataLoader for training data.
        cycle_number: Current cycle number.
        timeout_seconds: Maximum allowed time.
        modification_proposal: Optional proposal dict.
    
    Returns:
        Metrics dictionary.
    """
    return run_training_cycle_with_timeout(
        model,
        train_loader,
        cycle_number,
        timeout_seconds,
        modification_proposal
    )