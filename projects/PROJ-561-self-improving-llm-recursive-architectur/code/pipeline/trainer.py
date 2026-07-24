import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from typing import Optional, Dict, Any, Tuple
import time
import math
import os
import json
from datetime import datetime

from pipeline.loader import load_openwebtext
from pipeline.model import load_gpt_124m, save_model_state
from utils.logging import update_cycle_log, log_cycle_summary
from config import get_config

def count_flops(model: nn.Module, input_ids: torch.Tensor) -> int:
    """
    Estimate FLOPs for a forward pass.
    Approximation: 2 * num_params * seq_len (simplified for GPT).
    """
    num_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    seq_len = input_ids.shape[1]
    # 2 FLOPs per multiply-add, roughly 2 * params * seq_len for attention+ffn
    return int(2 * num_params * seq_len)

def train_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: torch.optim.Optimizer,
    scheduler: Optional[torch.optim.lr_scheduler._LRScheduler] = None,
    device: str = "cpu",
    max_steps: Optional[int] = None
) -> Tuple[float, float, int]:
    """
    Train one epoch. Returns (avg_loss, elapsed_time_seconds, total_flops).
    """
    model.train()
    total_loss = 0.0
    total_flops = 0
    steps = 0
    start_time = time.time()
    config = get_config()

    for batch_idx, batch in enumerate(dataloader):
        if max_steps and steps >= max_steps:
            break

        input_ids = batch["input_ids"].to(device)
        labels = batch["labels"].to(device)

        optimizer.zero_grad()

        outputs = model(input_ids, labels=labels)
        loss = outputs.loss

        # FLOP accounting
        flops = count_flops(model, input_ids)
        total_flops += flops

        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        if scheduler:
            scheduler.step()

        total_loss += loss.item()
        steps += 1

    elapsed = time.time() - start_time
    avg_loss = total_loss / steps if steps > 0 else 0.0
    return avg_loss, elapsed, total_flops

def _timeout_wrapper(func, timeout_seconds: int, cycle_id: str, partial_metrics_path: str):
    """
    Returns a wrapper that executes func, but if it exceeds timeout_seconds,
    kills the thread/process logic by raising TimeoutError and writing partial metrics.
    Note: In a pure Python CPU environment without multiprocessing, we cannot
    forcefully kill a running thread. We use a signal-based approach for Unix
    or a polling mechanism. For robustness in this specific research context,
    we will use a simple polling check inside the function if possible, or
    rely on the outer loop to catch TimeoutError if we spawn a process.
    
    However, to strictly adhere to "terminate cycle if exceeded" without complex
    multi-process setups that might break the single-file script requirement,
    we implement a check-interval wrapper. If the function is long-running,
    the caller must ensure it yields control or we use a signal alarm.
    
    Given the constraints of a single Python script on CPU, we will use
    signal.alarm for Unix-like systems to raise an exception.
    """
    import signal
    
    def handler(signum, frame):
        raise TimeoutError(f"Cycle {cycle_id} exceeded {timeout_seconds}s timeout")

    original_handler = signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout_seconds)
    try:
        result = func()
        signal.alarm(0)  # Cancel alarm
        return result
    except TimeoutError as e:
        # Log timeout and write partial metrics
        update_cycle_log(cycle_id, {"status": "Timeout", "error": str(e)})
        
        # Construct partial metrics object
        partial_data = {
            "cycle_id": cycle_id,
            "timestamp": datetime.now().isoformat(),
            "status": "Timeout",
            "error": str(e),
            "partial_metrics": {
                "training_time": timeout_seconds, # Approximate
                "loss": None,
                "flops": None,
                "gsm8k": None,
                "arc": None,
                "ece": None
            }
        }
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(partial_metrics_path), exist_ok=True)
        
        # Write partial metrics
        with open(partial_metrics_path, "w") as f:
            json.dump(partial_data, f, indent=2)
        
        log_cycle_summary(cycle_id, "Timeout", partial_data)
        raise e
    finally:
        signal.signal(signal.SIGALRM, original_handler)

def run_training_cycle(
    cycle_id: str,
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: torch.optim.Optimizer,
    scheduler: Optional[torch.optim.lr_scheduler._LRScheduler] = None,
    timeout_seconds: int = 3600,
    device: str = "cpu"
) -> Dict[str, Any]:
    """
    Execute a single training cycle with timeout enforcement.
    Returns metrics dict on success. Raises TimeoutError on timeout (after logging).
    """
    config = get_config()
    partial_metrics_path = os.path.join(config.path_config.results_dir, f"partial_cycle_{cycle_id}.json")
    
    # We need to wrap the training logic. Since train_epoch is the heavy part,
    # we wrap the call to it.
    
    def training_task():
        # Reset memory if needed (T004 logic)
        from utils.memory import check_and_terminate_if_exceeds
        check_and_terminate_if_exceeds(limit_gb=7.0)
        
        # Train
        loss, elapsed_time, total_flops = train_epoch(
            model, dataloader, optimizer, scheduler, device
        )
        
        return {
            "cycle_id": cycle_id,
            "status": "Success",
            "loss": loss,
            "training_time_seconds": elapsed_time,
            "total_flops": total_flops,
            "timestamp": datetime.now().isoformat()
        }

    try:
        # Apply timeout wrapper
        result = _timeout_wrapper(training_task, timeout_seconds, cycle_id, partial_metrics_path)
        log_cycle_summary(cycle_id, "Success", result)
        return result
    except TimeoutError:
        # Re-raise to let the caller (main.py) handle the flow (e.g., early stop)
        raise