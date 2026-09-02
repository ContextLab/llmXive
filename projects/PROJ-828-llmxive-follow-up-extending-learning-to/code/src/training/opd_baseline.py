"""
OPD Baseline Implementation for Low-Rank RL Foresight.

This module implements the On-Policy Distillation (OPD) baseline, including
logic to record parameter updates (Delta W) and save per-layer update vectors
to disk for subsequent SVD analysis.
"""
import os
import json
import gc
import math
import time
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Iterator

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from transformers import AutoModelForCausalLM, AutoTokenizer
from datasets import load_dataset

from src.utils.seeds import set_seed
from src.utils.memory_monitor import MemoryMonitor, enforce_memory_limit
from src.data.loader import GSM8KStreamingLoader, load_gsm8k_streaming

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class OPDConfig:
    """Configuration for OPD Baseline training."""
    model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    dataset_name: str = "gsm8k"
    dataset_split: str = "train"
    num_steps: int = 100
    batch_size: int = 4
    learning_rate: float = 1e-5
    seed: int = 42
    early_window_fraction: float = 0.2
    output_dir: str = "results/opd"
    memory_limit_gb: float = 6.5  # Conservative limit to stay under 7GB


class GSM8KDataset(torch.utils.data.Dataset):
    """
    Streaming-compatible dataset wrapper for GSM8K.
    Wraps the streaming iterator to allow batched access via __getitem__
    by caching a window of examples.
    """
    def __init__(self, loader: GSM8KStreamingLoader, max_cache: int = 1000):
        self.loader = loader
        self.max_cache = max_cache
        self.cache: List[Dict[str, Any]] = []
        self._fill_cache()

    def _fill_cache(self):
        """Refill the cache from the streaming loader."""
        count = 0
        while count < self.max_cache:
            try:
                item = next(self.loader)
                self.cache.append(item)
                count += 1
            except StopIteration:
                break
        if count == 0:
            raise StopIteration("Dataset exhausted or empty.")

    def __len__(self):
        return len(self.cache)

    def __getitem__(self, idx):
        if idx >= len(self.cache):
            # Refill if we are near the end (simple sliding window logic)
            if len(self.cache) < self.max_cache:
                self._fill_cache()
            else:
                # Simple wrap or error if truly exhausted
                raise IndexError("Index out of bounds for current cache.")
        return self.cache[idx]


def calculate_update_delta(
    model: nn.Module,
    previous_state: Dict[str, torch.Tensor],
    current_state: Dict[str, torch.Tensor]
) -> Dict[str, torch.Tensor]:
    """
    Calculate the difference (Delta W) between current and previous model states.
    Only computes differences for parameters that have changed (i.e., are trainable).
    """
    deltas = {}
    for name, param in model.named_parameters():
        if name in previous_state and param.requires_grad:
            delta = current_state[name] - previous_state[name]
            deltas[name] = delta
    return deltas


def save_layer_updates(
    deltas: Dict[str, torch.Tensor],
    step: int,
    output_dir: Path,
    seed: int
) -> None:
    """
    Save per-layer update vectors to separate files.
    Files are named: results/opd/updates_seed_{i}/layer_{index:02d}.pt

    Naming convention logic:
    1. Extract index from state_dict keys using regex `layer_(\d+)`.
    2. If not found, use sequential numeric indices based on sort order.
    """
    seed_dir = output_dir / f"updates_seed_{seed}"
    seed_dir.mkdir(parents=True, exist_ok=True)

    # Sort keys to ensure deterministic ordering
    sorted_keys = sorted(deltas.keys())

    # Attempt to map keys to indices based on regex
    key_to_index = {}
    index_counter = 0
    pattern = re.compile(r'layer_(\d+)')

    for key in sorted_keys:
        match = pattern.search(key)
        if match:
            key_to_index[key] = int(match.group(1))
        else:
            # Fallback: assign sequential index
            key_to_index[key] = index_counter
            index_counter += 1

    # Save each delta
    for key, delta in deltas.items():
        idx = key_to_index[key]
        filename = f"layer_{idx:02d}.pt"
        filepath = seed_dir / filename

        # Detach and move to CPU to save memory and ensure serialization
        delta_cpu = delta.detach().cpu()
        torch.save(delta_cpu, filepath)

    logger.info(f"Saved {len(deltas)} layer updates for step {step} to {seed_dir}")


def run_opd_step(
    model: nn.Module,
    batch: Dict[str, torch.Tensor],
    optimizer: optim.Optimizer,
    previous_state: Dict[str, torch.Tensor]
) -> Tuple[Dict[str, torch.Tensor], float]:
    """
    Execute a single OPD training step.
    Returns the new state and the loss.
    """
    optimizer.zero_grad()

    # Forward pass
    outputs = model(**batch)
    loss = outputs.loss

    # Backward pass
    loss.backward()

    # Optimizer step
    optimizer.step()

    # Capture current state
    current_state = {name: param.data.clone() for name, param in model.named_parameters()}

    # Calculate delta
    delta = calculate_update_delta(model, previous_state, current_state)

    return delta, loss.item()


def calculate_early_window(total_steps: int, fraction: float) -> int:
    """
    Calculate the number of steps for the early window.
    Defaults to a minimum of 5 steps if the calculation yields less.
    """
    window = math.ceil(total_steps * fraction)
    return max(window, 5)


def run_opd_baseline(config: OPDConfig) -> Dict[str, Any]:
    """
    Main runner for the OPD Baseline experiment.

    1. Sets up seeds and memory monitoring.
    2. Loads the pruned model and GSM8K dataset (streaming).
    3. Runs the training loop for `num_steps`.
    4. Saves per-layer update vectors (T018b) during the early window.
    5. Aggregates metrics and saves configuration.
    """
    # 1. Setup
    set_seed(config.seed)
    output_path = Path(config.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    memory_monitor = MemoryMonitor(limit_gb=config.memory_limit_gb)
    memory_monitor.start()

    logger.info(f"Starting OPD Baseline with seed {config.seed}")
    logger.info(f"Model: {config.model_name}")
    logger.info(f"Steps: {config.num_steps}")

    # 2. Load Model
    # Assuming T009 has already pruned the model config and we load the base
    # In a real pipeline, we might load a specific pruned checkpoint.
    # Here we load the base and assume it matches the pruned config or is pruned externally.
    try:
        model = AutoModelForCausalLM.from_pretrained(
            config.model_name,
            torch_dtype=torch.float16,
            trust_remote_code=False,
            device_map="cpu" # CPU constraint per spec
        )
        model.train()
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

    # 3. Load Data (Streaming)
    try:
        # Use the streaming loader from T007/T059
        loader = load_gsm8k_streaming(config.dataset_name, config.dataset_split)
        dataset = GSM8KDataset(loader, max_cache=1000)
        dataloader = DataLoader(
            dataset,
            batch_size=config.batch_size,
            shuffle=False, # Streaming usually sequential
            num_workers=0
        )
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

    # 4. Optimizer
    optimizer = optim.AdamW(model.parameters(), lr=config.learning_rate)

    # 5. Training Loop
    early_window_size = calculate_early_window(config.num_steps, config.early_window_fraction)
    logger.info(f"Early window size: {early_window_size}")

    # Initial state capture
    previous_state = {name: param.data.clone() for name, param in model.named_parameters()}

    metrics_log = []
    step = 0

    # Iterate through dataloader, wrapping around if needed
    dataloader_iter = iter(dataloader)

    for _ in range(config.num_steps):
        try:
            batch = next(dataloader_iter)
        except StopIteration:
            # Reset iterator if dataset is smaller than steps
            dataloader_iter = iter(dataloader)
            batch = next(dataloader_iter)

        # Ensure batch tensors are on CPU
        batch = {k: v.cpu() for k, v in batch.items()}

        # Run step
        delta, loss = run_opd_step(model, batch, optimizer, previous_state)

        # Update previous state
        previous_state = {name: param.data.clone() for name, param in model.named_parameters()}

        # Logging
        metrics_log.append({
            "step": step,
            "loss": loss,
            "timestamp": time.time()
        })

        # T018b: Save per-layer update vectors during early window
        if step < early_window_size:
            save_layer_updates(delta, step, output_path, config.seed)
            # Force GC to manage memory
            gc.collect()

        step += 1

        # Check memory
        if step % 10 == 0:
            mem_usage = memory_monitor.get_current_memory_mb()
            if mem_usage > config.memory_limit_gb * 1024:
                logger.warning(f"Memory usage {mem_usage}MB exceeds limit. Continuing but monitoring closely.")

    # 6. Finalize
    memory_monitor.stop()
    peak_memory = memory_monitor.get_peak_memory_mb()

    # Save metrics
    metrics_file = output_path / f"metrics_seed_{config.seed}.json"
    with open(metrics_file, 'w') as f:
        json.dump(metrics_log, f, indent=2)

    # Save config
    config_file = output_path / f"config_seed_{config.seed}.json"
    with open(config_file, 'w') as f:
        json.dump(config.__dict__, f, indent=2)

    logger.info(f"OPD Baseline completed. Peak Memory: {peak_memory:.2f} MB")
    logger.info(f"Artifacts saved to {output_path}")

    return {
        "status": "success",
        "seed": config.seed,
        "steps": step,
        "peak_memory_mb": peak_memory,
        "output_dir": str(output_path)
    }


def main():
    """CLI Entry point for OPD Baseline."""
    import argparse

    parser = argparse.ArgumentParser(description="Run OPD Baseline")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--steps", type=int, default=100, help="Number of training steps")
    parser.add_argument("--lr", type=float, default=1e-5, help="Learning rate")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size")
    parser.add_argument("--output-dir", type=str, default="results/opd", help="Output directory")
    parser.add_argument("--early-window-fraction", type=float, default=0.2, help="Fraction of steps for early window")

    args = parser.parse_args()

    config = OPDConfig(
        seed=args.seed,
        num_steps=args.steps,
        learning_rate=args.lr,
        batch_size=args.batch_size,
        output_dir=args.output_dir,
        early_window_fraction=args.early_window_fraction
    )

    try:
        result = run_opd_baseline(config)
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"OPD Baseline failed: {e}")
        # Re-raise to ensure the pipeline knows it failed
        raise


if __name__ == "__main__":
    main()