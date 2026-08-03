import os
import json
import gc
import math
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import torch
import torch.nn as nn
import torch.optim as optim
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import get_peft_model, LoraConfig, TaskType

# Import from project API surface
from src.utils.seeds import set_seed, generate_seed_from_string
from src.utils.memory_monitor import MemoryMonitor
from src.utils.hasher import compute_file_hash
from src.models.config import prune_model_to_target_params
from src.data.loader import load_gsm8k_subset

# Constants
DEFAULT_TARGET_PARAMS = 300_000_000  # 300M
PARAM_TOLERANCE = 0.05  # 5%
DEFAULT_TOTAL_STEPS = 500
DEFAULT_BATCH_SIZE = 4
DEFAULT_LEARNING_RATE = 1e-4
DEFAULT_MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"


class GSM8KDataset(torch.utils.data.Dataset):
    """Dataset wrapper for GSM8K problems."""
    def __init__(self, data: List[Dict[str, str]], tokenizer: AutoTokenizer, max_length: int = 512):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        # Format: "Question: {question} Answer: {answer}"
        prompt = f"Question: {item['question']} Answer: {item['answer']}"
        encoded = self.tokenizer(
            prompt,
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt"
        )
        return {
            "input_ids": encoded["input_ids"].squeeze(0),
            "attention_mask": encoded["attention_mask"].squeeze(0),
            "labels": encoded["input_ids"].squeeze(0).clone()  # Teacher forcing
        }


def calculate_update_delta(
    model: nn.Module,
    old_state_dict: Dict[str, torch.Tensor],
    new_state_dict: Dict[str, torch.Tensor]
) -> Dict[str, torch.Tensor]:
    """
    Calculate the difference (delta) between current and previous weights.
    Returns a dict of {layer_name: delta_tensor}.
    """
    deltas = {}
    for name, param in model.named_parameters():
        if name in old_state_dict:
            delta = param.data.detach().clone() - old_state_dict[name]
            deltas[name] = delta
    return deltas


def save_layer_updates(
    deltas: Dict[str, torch.Tensor],
    output_dir: Path,
    step: int,
    seed: int
) -> List[Path]:
    """
    Save per-layer update vectors to separate files to ensure memory compliance.
    Format: results/opd/updates_seed_{i}/layer_{l}.pt
    """
    seed_dir = output_dir / f"updates_seed_{seed}"
    seed_dir.mkdir(parents=True, exist_ok=True)

    saved_files = []
    for layer_name, delta in deltas.items():
        # Sanitize layer name for filename
        safe_name = layer_name.replace(".", "_").replace("/", "_")
        file_path = seed_dir / f"layer_{step}_{safe_name}.pt"
        torch.save(delta, file_path)
        saved_files.append(file_path)

    return saved_files


def run_opd_step(
    model: nn.Module,
    batch: Dict[str, torch.Tensor],
    optimizer: optim.Optimizer,
    old_state_dict: Dict[str, torch.Tensor]
) -> Tuple[Dict[str, torch.Tensor], float]:
    """
    Execute one training step and return the weight update delta and loss.
    """
    optimizer.zero_grad()
    input_ids = batch["input_ids"]
    labels = batch["labels"]
    attention_mask = batch["attention_mask"]

    outputs = model(
        input_ids=input_ids,
        attention_mask=attention_mask,
        labels=labels
    )
    loss = outputs.loss
    loss.backward()
    optimizer.step()

    # Calculate delta after update
    new_state_dict = {k: v.detach().clone() for k, v in model.named_parameters()}
    delta = calculate_update_delta(model, old_state_dict, new_state_dict)

    # Update old state for next step
    for name, param in model.named_parameters():
        old_state_dict[name] = param.detach().clone()

    return delta, loss.item()


def calculate_early_window(total_steps: int) -> int:
    """
    Define the 'early' trajectory window.
    Logic: max(50, ceil(total_steps * 0.10))
    """
    return max(50, math.ceil(total_steps * 0.10))


def run_opd_baseline(
    seed: int,
    total_steps: int = DEFAULT_TOTAL_STEPS,
    batch_size: int = DEFAULT_BATCH_SIZE,
    learning_rate: float = DEFAULT_LEARNING_RATE,
    output_dir: Path = Path("results"),
    model_name: str = DEFAULT_MODEL_NAME
) -> Dict[str, Any]:
    """
    Run the On-Policy Distillation (OPD) baseline.
    Records Delta W matrices for the initial phase of training.
    Saves list of tensors to results/opd/updates_seed_{i}.pt
    """
    # Set seed for determinism
    set_seed(seed)

    # Initialize memory monitor
    memory_monitor = MemoryMonitor(limit_bytes=7 * 1024**3)  # 7GB limit
    memory_monitor.start()

    # Create output directories
    opd_dir = output_dir / "opd"
    opd_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    print(f"Loading GSM8K subset for seed {seed}...")
    dataset = load_gsm8k_subset()
    if len(dataset) < 1000:
        raise ValueError(f"Dataset too small: {len(dataset)}")

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    gsm_dataset = GSM8KDataset(dataset, tokenizer)
    dataloader = torch.utils.data.DataLoader(
        gsm_dataset, batch_size=batch_size, shuffle=True
    )

    # Load and prune model
    print(f"Loading and pruning model: {model_name}...")
    base_model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float32,
        device_map="cpu"
    )
    base_model = prune_model_to_target_params(
        base_model,
        target_params=DEFAULT_TARGET_PARAMS,
        tolerance=PARAM_TOLERANCE
    )

    # Initialize optimizer
    optimizer = optim.AdamW(base_model.parameters(), lr=learning_rate)

    # Initialize state tracking
    old_state_dict = {k: v.detach().clone() for k, v in base_model.named_parameters()}
    all_deltas = []  # Accumulate deltas for the summary file
    early_window = calculate_early_window(total_steps)
    memory_log = []

    print(f"Starting OPD training for {total_steps} steps (Early window: {early_window})...")
    start_time = time.time()

    step = 0
    for epoch in range(100):  # Limit epochs
        for batch in dataloader:
            if step >= total_steps:
                break

            # Move batch to CPU
            batch = {k: v.to("cpu") for k, v in batch.items()}

            # Run step
            delta, loss = run_opd_step(base_model, batch, optimizer, old_state_dict)
            all_deltas.append(delta)

            # Log per-step updates (T018b requirement)
            if step % 10 == 0:  # Log every 10 steps to save I/O
                save_layer_updates(delta, opd_dir, step, seed)

            # Memory check
            if step % 50 == 0:
                mem_usage = memory_monitor.get_current_usage()
                memory_log.append({"step": step, "ram_mb": mem_usage / (1024**2)})
                if mem_usage > 7 * 1024**3:
                    raise RuntimeError(f"Memory limit exceeded at step {step}: {mem_usage / (1024**3):.2f} GB")

            step += 1
            if step >= total_steps:
                break

        if step >= total_steps:
            break

    elapsed_time = time.time() - start_time
    peak_memory = memory_monitor.get_peak_usage()

    # Save aggregated deltas for the seed
    # T018 requirement: Save list of tensors to results/opd/updates_seed_{i}.pt
    # We save the accumulated deltas for the early window or full run
    output_file = opd_dir / f"updates_seed_{seed}.pt"
    torch.save(all_deltas, output_file)

    # Write early window config
    config_file = output_dir / "early_window_config.json"
    with open(config_file, "w") as f:
        json.dump({
            "total_steps": total_steps,
            "early_window": early_window,
            "formula": "max(50, ceil(total_steps * 0.10))"
        }, f, indent=2)

    # Write memory profile
    memory_file = output_dir / "memory_profile.json"
    with open(memory_file, "w") as f:
        json.dump({
            "seed": seed,
            "peak_memory_mb": peak_memory / (1024**2),
            "log": memory_log
        }, f, indent=2)

    # Compute hash of output
    output_hash = compute_file_hash(output_file)

    print(f"OPD Baseline completed for seed {seed} in {elapsed_time:.2f}s")
    print(f"Output saved to: {output_file}")
    print(f"Hash: {output_hash}")

    return {
        "seed": seed,
        "steps": step,
        "early_window": early_window,
        "output_file": str(output_file),
        "hash": output_hash,
        "peak_memory_mb": peak_memory / (1024**2),
        "elapsed_time": elapsed_time
    }


def main():
    """Entry point for running OPD baseline."""
    import argparse

    parser = argparse.ArgumentParser(description="Run OPD Baseline")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--steps", type=int, default=DEFAULT_TOTAL_STEPS, help="Total training steps")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="Batch size")
    parser.add_argument("--lr", type=float, default=DEFAULT_LEARNING_RATE, help="Learning rate")
    parser.add_argument("--output-dir", type=str, default="results", help="Output directory")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL_NAME, help="Base model name")

    args = parser.parse_args()

    result = run_opd_baseline(
        seed=args.seed,
        total_steps=args.steps,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        output_dir=Path(args.output_dir),
        model_name=args.model
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()