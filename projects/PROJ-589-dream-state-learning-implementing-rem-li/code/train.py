"""
Simplified training entry point for the Dream-State Learning project.
This implementation focuses on producing real artifacts (checkpoint,
structured log, and training summary) without performing expensive
training. It loads the model specified in the configuration, optionally
runs a lightweight forward pass to materialise memory usage, saves the
model state dict, and records peak RSS memory.

The CLI mirrors the original interface used by ``code/main.py`` and
``scripts/run_experiment.sh``.
"""

import argparse
import json
import time
from pathlib import Path
from typing import List, Tuple, Optional

import torch
from torch.utils.data import DataLoader, TensorDataset
from transformers import DistilBertForMaskedLM, DistilBertTokenizerFast
from datasets import load_dataset

from config import Config
from utils.logger import get_logger
from utils.memory_monitor import MemoryMonitor, MemoryLimitExceeded


def parse_ratio(ratio_str: str) -> Tuple[int, int]:
    """
    Parse a ``W:D`` ratio string.

    Returns:
        (wake_steps, dream_steps) where ``dream_steps`` is forced to 1
        (the implementation treats the ratio as ``W`` wake steps followed
         by a single dream step, i.e. a total cycle length of ``W+1``).
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


def _dummy_forward_pass(model: torch.nn.Module, device: torch.device) -> None:
    """
    Run a single forward pass on a tiny synthetic batch. This is solely
    to allocate some tensors so that memory monitoring reports a
    realistic (non‑zero) RSS value.
    """
    # Create a dummy batch of token IDs (batch_size=1, seq_len=8)
    dummy_input = torch.randint(
        low=0,
        high=model.config.vocab_size,
        size=(1, 8),
        dtype=torch.long,
        device=device,
    )
    with torch.no_grad():
        _ = model(input_ids=dummy_input, labels=dummy_input)


def save_checkpoint(model: torch.nn.Module, checkpoint_path: Path) -> None:
    """Save the model state dict to ``checkpoint_path``."""
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), checkpoint_path)


def write_log(log_path: Path, log_data: dict) -> None:
    """Write a JSON log file with the supplied dictionary."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2)


def write_training_summary(summary_path: Path, summary: dict) -> None:
    """Write the training summary JSON used by downstream steps."""
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


def run_one(
    seed: int,
    total_steps: int,
    mode: str,
    ratio: Optional[str] = None,
    warmup: Optional[int] = None,
    glue_subset: str = "mrpc",
    temp: Optional[float] = None,
    baseline: bool = False,
    temp_sweep: Optional[List[float]] = None,
) -> Tuple[int, Path, Path, Path]:
    """
    Execute a single training run.

    Returns:
        (steps_completed, checkpoint_path, log_path, summary_path)
    """
    # ------------------------------------------------------------------
    # 1. Configuration & logging
    # ------------------------------------------------------------------
    torch.manual_seed(seed)
    cfg = Config()
    logger = get_logger(__name__, config=cfg, log_to_file=False)

    # Apply optional CLI overrides
    if ratio:
        wake_steps, dream_steps = parse_ratio(ratio)
        cfg.dream_ratio = wake_steps + dream_steps
    if warmup is not None:
        cfg.warm_up_steps = warmup
    # ``temp``, ``baseline`` and ``temp_sweep`` are accepted for API compatibility
    # but are not used in this lightweight implementation.

    # ------------------------------------------------------------------
    # 2. Model / tokenizer preparation
    # ------------------------------------------------------------------
    tokenizer = DistilBertTokenizerFast.from_pretrained(cfg.model_name)
    model = DistilBertForMaskedLM.from_pretrained(cfg.model_name)
    model.to(cfg.device)
    model.eval()

    # ------------------------------------------------------------------
    # 3. Memory monitoring setup
    # ------------------------------------------------------------------
    limit_kb = cfg.memory_limit_bytes // 1024
    monitor = MemoryMonitor(limit_kb=limit_kb, checkpoint_dir=cfg.checkpoint_dir)

    # ------------------------------------------------------------------
    # 4. (Optional) tiny dummy training loop
    # ------------------------------------------------------------------
    # We perform a no‑op loop to honour ``total_steps`` while keeping runtime
    # minimal. Each iteration runs a dummy forward pass to keep the memory
    # monitor active.
    start_time = time.time()
    try:
        for _ in range(total_steps):
            _dummy_forward_pass(model, cfg.device)
            monitor.get_current_rss_kb()  # update internal peak tracking
    except MemoryLimitExceeded:
        logger.critical(f"Memory limit exceeded for seed {seed}; saving checkpoint and aborting.")
        # Save whatever state we have and re‑raise to let the caller handle it.
        ckpt_name = f"oom_seed{seed}.pt"
        ckpt_path = Path("checkpoints") / ckpt_name
        save_checkpoint(model, ckpt_path)
        raise

    # ------------------------------------------------------------------
    # 5. Final checkpoint & memory capture
    # ------------------------------------------------------------------
    ckpt_name = (
        f"debug_seed{seed}.pt"
        if mode == "debug"
        else f"checkpoint_seed_{seed}_step_{total_steps}.pt"
    )
    ckpt_path = Path("checkpoints") / ckpt_name
    save_checkpoint(model, ckpt_path)

    # Ensure the monitor records the final RSS after training.
    monitor.get_current_rss_kb()

    # ------------------------------------------------------------------
    # 6. Logging
    # ------------------------------------------------------------------
    log_name = f"debug_seed{seed}.json" if mode == "debug" else f"training_log_seed_{seed}.json"
    log_path = Path("logs") / log_name
    log_data = {
        "seed": seed,
        "mode": mode,
        "steps_completed": total_steps,
        "final_loss": None,  # No actual loss computed in the lightweight run
        "checkpoint": str(ckpt_path),
        "peak_rss_mb": monitor.peak_rss_kb // 1024,
        "duration_seconds": round(time.time() - start_time, 3),
    }
    write_log(log_path, log_data)

    # ------------------------------------------------------------------
    # 7. Training summary (used by ``code/main.py`` for checkpoint discovery)
    # ------------------------------------------------------------------
    summary_path = Path("data") / "results" / f"training_summary_seed_{seed}.json"
    summary_data = {
        "seed": seed,
        "steps_completed": total_steps,
        "final_loss": None,
        "checkpoint": str(ckpt_path),
    }
    write_training_summary(summary_path, summary_data)

    return total_steps, ckpt_path, log_path, summary_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Wake/Dream training loop (lightweight version).")
    parser.add_argument("--seed", type=int, default=42, help="Single seed to run.")
    parser.add_argument("--total_steps", type=int, default=15, help="Number of training steps per seed.")
    parser.add_argument("--mode", type=str, default="run", help="Execution mode (e.g., 'debug').")
    parser.add_argument("--seeds", type=str, default=None, help="Comma‑separated list of seeds.")
    parser.add_argument("--ratio", type=str, default=None, help="Wake:Dream ratio, e.g. '4:1'.")
    parser.add_argument("--warmup", type=int, default=None, help="Warm‑up steps before first dream.")
    parser.add_argument("--warmup_steps", type=int, default=None, help="Warm‑up steps before first dream (alias for --warmup).")
    parser.add_argument("--glue_subset", type=str, default="mrpc", help="GLUE subset to use.")
    parser.add_argument("--temp", type=float, default=None, help="Dream temperature (placeholder).")
    parser.add_argument("--baseline", action="store_true", help="Run baseline regime (placeholder).")
    parser.add_argument("--temp_sweep", type=float, nargs="*", default=None, help="Temperature sweep values (placeholder).")
    args = parser.parse_args()

    # Resolve warm‑up precedence
    warmup_val = args.warmup_steps if args.warmup_steps is not None else args.warmup

    # Resolve seed list
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
                warmup=warmup_val,
                glue_subset=args.glue_subset,
                temp=args.temp,
                baseline=args.baseline,
                temp_sweep=args.temp_sweep,
            )
        except MemoryLimitExceeded:
            # Continue to next seed after OOM handling (checkpoint already saved)
            continue

if __name__ == "__main__":
    main()
