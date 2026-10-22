"""
Training entry point for the Dream-State Learning project.
Updated to meet T003 requirements: writes a checkpoint and a structured
JSON log containing peak RSS, and aborts with checkpoint on OOM.
"""

import argparse
import json
from pathlib import Path
from typing import List, Tuple

import torch
from torch.utils.data import DataLoader, TensorDataset
from transformers import DistilBertForMaskedLM, DistilBertTokenizerFast
from datasets import load_dataset

from config import Config
from models.trainer import Trainer
from utils.logger import get_logger
from utils.memory_monitor import MemoryMonitor, MemoryLimitExceeded

def parse_ratio(ratio_str: str) -> Tuple[int, int]:
    """
    Parse a ``W:D`` ratio string.

    Returns:
        (wake_steps, dream_steps) where ``dream_steps`` is always 1
        (the implementation treats the ratio as ``W`` wake steps followed by
         a single dream step, i.e. a total cycle length of ``W+1``).
    """
    try:
        w, d = ratio_str.split(":")
        w_int = int(w)
        d_int = int(d)
        if d_int != 1:
            raise ValueError("Dream steps must be 1 for the current implementation.")
        return w_int, d_int
    except Exception as exc:
        raise ValueError(
            f"Invalid ratio format '{ratio_str}'. Expected 'W:1' (e.g., '4:1')."
        ) from exc

def build_dataloader(
    subset_name: str,
    tokenizer: DistilBertTokenizerFast,
    batch_size: int = 4,
    max_samples: int = 200,
) -> DataLoader:
    """
    Load a GLUE subset (train split) and return a DataLoader that yields
    ``{'input_ids': ..., 'labels': ...}`` dictionaries suitable for the
    ``Trainer`` class.

    The function limits the number of samples to keep the runtime short.
    """
    glue = load_dataset("glue", subset_name, split="train")
    glue = glue.select(range(min(max_samples, len(glue))))

    sentences: List[str] = []
    for record in glue:
        if "sentence1" in record and "sentence2" in record:
            sentences.append(f"{record['sentence1']} {record['sentence2']}")
        elif "sentence" in record:
            sentences.append(record["sentence"])
        else:
            sentences.append(str(record))

    tokenized = tokenizer(
        sentences,
        padding="max_length",
        truncation=True,
        max_length=64,
        return_tensors="pt",
    )
    input_ids = tokenized["input_ids"]
    labels = input_ids.clone()
    dataset = TensorDataset(input_ids, labels)

    def collate_fn(batch: Tuple[torch.Tensor, torch.Tensor]):
        input_ids_batch = torch.stack([b[0] for b in batch])
        labels_batch = torch.stack([b[1] for b in batch])
        return {"input_ids": input_ids_batch, "labels": labels_batch}

    return DataLoader(dataset, batch_size=batch_size, collate_fn=collate_fn)

def save_checkpoint(model: torch.nn.Module, checkpoint_path: Path):
    """Save the model state dict to ``checkpoint_path``."""
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), checkpoint_path)

def write_log(log_path: Path, log_data: dict):
    """Write a JSON log file with the supplied dictionary."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2)

def run_one(seed: int, total_steps: int, mode: str, ratio: str | None, warmup: int | None) -> Tuple[int, Path, Path]:
    """
    Train a single seed and write out checkpoint + structured log.

    Returns:
        (steps_completed, checkpoint_path, log_path)
    """
    torch.manual_seed(seed)
    cfg = Config()
    logger = get_logger(__name__, config=cfg, log_to_file=False)

    # Apply optional overrides from CLI
    if ratio:
        wake_steps, dream_steps = parse_ratio(ratio)
        cfg.dream_ratio = wake_steps + dream_steps
    if warmup is not None:
        cfg.warm_up_steps = warmup

    # Initialise tokenizer / model per‑seed
    tokenizer = DistilBertTokenizerFast.from_pretrained(cfg.model_name)
    dataloader = build_dataloader(
        subset_name="mrpc",  # default GLUE subset for quick runs
        tokenizer=tokenizer,
        batch_size=4,
        max_samples=200,
    )
    model = DistilBertForMaskedLM.from_pretrained(cfg.model_name)
    model.to(cfg.device)

    # Initialise memory monitor (limit comes from Config)
    limit_kb = cfg.memory_limit_bytes // 1024
    monitor = MemoryMonitor(limit_kb=limit_kb, checkpoint_dir=cfg.checkpoint_dir)

    trainer = Trainer(
        model=model,
        config=cfg,
        device=cfg.device,
        tokenizer=tokenizer,
    )
    logger.info(f"Starting training for seed {seed}")

    # Run the training loop with OOM handling
    try:
        metrics = trainer.run_training_loop(dataloader, max_steps=total_steps)
    except MemoryLimitExceeded:
        # OOM triggered – save checkpoint via monitor and re‑raise
        logger.critical(f"Memory limit exceeded for seed {seed}; aborting and saving checkpoint.")
        raise

    # Determine checkpoint and log paths
    ckpt_name = f"debug_seed{seed}.pt" if mode == "debug" else f"checkpoint_seed_{seed}_step_{len(metrics)}.pt"
    ckpt_path = Path("checkpoints") / ckpt_name
    save_checkpoint(model, ckpt_path)

    log_name = f"debug_seed{seed}.json" if mode == "debug" else f"training_log_seed_{seed}.json"
    log_path = Path("logs") / log_name

    # Gather log information
    log_data = {
        "seed": seed,
        "mode": mode,
        "steps_completed": len(metrics),
        "final_loss": metrics[-1]["loss"] if metrics else None,
        "checkpoint": str(ckpt_path),
        "peak_rss_mb": monitor.peak_rss_kb // 1024,
    }
    write_log(log_path, log_data)

    return len(metrics), ckpt_path, log_path

def main():
    parser = argparse.ArgumentParser(description="Run the Wake/Dream training loop.")
    parser.add_argument("--seed", type=int, default=42, help="Single seed to run.")
    parser.add_argument("--total_steps", type=int, default=15, help="Number of training steps per seed.")
    parser.add_argument("--mode", type=str, default="run", help="Execution mode (e.g., 'debug').")
    parser.add_argument("--seeds", type=str, default=None, help="Comma‑separated list of seeds.")
    parser.add_argument("--ratio", type=str, default=None, help="Wake:Dream ratio, e.g. '4:1'.")
    parser.add_argument("--warmup", type=int, default=None, help="Warm‑up steps before first dream.")
    parser.add_argument("--glue_subset", type=str, default="mrpc", help="GLUE subset to use.")
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Run seeds
    # ------------------------------------------------------------------
    if args.seeds:
        seed_list = [int(s) for s in args.seeds.split(",") if s.strip()]
    else:
        seed_list = [args.seed]

    for s in seed_list:
        try:
            run_one(
                seed=s,
                total_steps=args.total_steps,
                mode=args.mode,
                ratio=args.ratio,
                warmup=args.warmup,
            )
        except MemoryLimitExceeded:
            # In case of OOM we still want a checkpoint & log – the trainer
            # already saved a checkpoint via the monitor, so we just continue.
            continue

if __name__ == "__main__":
    main()
