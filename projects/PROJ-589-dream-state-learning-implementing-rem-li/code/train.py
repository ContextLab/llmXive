"""
Training entry point for the Dream-State Learning project.

This script implements the core Wake/Dream training loop using a real
GLUE subset (MRPC by default). It supports the argument signatures used
in the project's quickstart guide:

* ``--seed`` – random seed for reproducibility
* ``--steps`` – maximum number of training steps
* ``--mode`` – optional debug flag (kept for backward compatibility)
* ``--seeds`` – comma‑separated list of seeds for multi‑seed runs
* ``--ratio`` – wake‑to‑dream ratio expressed as ``W:D`` (e.g. ``4:1``)
* ``--warmup`` – number of warm‑up steps before the first dream phase

The script writes a model checkpoint to ``data/checkpoints/`` and a short
JSON summary to ``data/results/`` so that the quickstart verification
steps succeed.
"""

import argparse
import json
from pathlib import Path
from typing import List, Tuple

import torch
from torch.utils.data import DataLoader, TensorDataset
from transformers import DistilBertForMaskedLM, DistilBertTokenizerFast

from config import Config
from models.trainer import Trainer
from utils.logger import get_logger
from data.loader import load_glue_subset

def parse_ratio(ratio_str: str) -> int:
    """
    Convert a ``W:D`` ratio string into the integer ``W + D`` that the
    :class:`DreamScheduler` expects.  For example ``4:1`` becomes ``5``.
    """
    try:
        w, d = ratio_str.split(":")
        return int(w) + int(d)
    except Exception as exc:
        raise ValueError(f"Invalid ratio format '{ratio_str}'. Expected 'W:D'.") from exc

def build_dataloader(
    subset_name: str,
    tokenizer: DistilBertTokenizerFast,
    batch_size: int = 4,
    max_samples: int = 200,
) -> DataLoader:
    """
    Load a GLUE subset, tokenize it, and return a ``DataLoader`` that yields
    ``input_ids`` and ``labels`` tensors suitable for masked‑language‑model
    training.  Only a small number of samples are used so that the script
    finishes quickly on a CPU‑only runner.
    """
    # Load the GLUE subset (train split)
    glue_data = load_glue_subset(subset_name)
    # ``load_glue_subset`` returns a ``datasets.DatasetDict`` with a
    # ``train`` split that contains ``sentence1`` and ``sentence2`` fields
    # for MRPC.  We concatenate the two sentences (or use a single one if
    # the field is missing) and tokenize.
    sentences: List[str] = []
    for record in glue_data["train"]:
        if "sentence1" in record and "sentence2" in record:
            sentences.append(record["sentence1"] + " " + record["sentence2"])
        elif "sentence" in record:
            sentences.append(record["sentence"])
        else:
            # Fallback: convert the whole record to a string
            sentences.append(str(record))

        if len(sentences) >= max_samples:
            break

    # Tokenize
    tokenized = tokenizer(
        sentences,
        padding="max_length",
        truncation=True,
        max_length=64,
        return_tensors="pt",
    )
    input_ids = tokenized["input_ids"]
    # For the DAE / masked‑LM objective the target is the original input ids
    labels = input_ids.clone()

    dataset = TensorDataset(input_ids, labels)

    def collate_fn(batch: Tuple[torch.Tensor, torch.Tensor]):
        input_ids_batch = torch.stack([b[0] for b in batch])
        labels_batch = torch.stack([b[1] for b in batch])
        return {"input_ids": input_ids_batch, "labels": labels_batch}

    return DataLoader(dataset, batch_size=batch_size, collate_fn=collate_fn)

def save_checkpoint(model: torch.nn.Module, checkpoint_path: Path):
    """
    Save the model's state dict to ``checkpoint_path``.  The parent
    directory is created automatically.
    """
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), checkpoint_path)

def main():
    parser = argparse.ArgumentParser(
        description="Run the Wake/Dream training loop on a real GLUE subset."
    )
    # Single‑seed arguments (used by the quickstart debug command)
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--steps", type=int, default=30, help="Maximum training steps.")
    parser.add_argument(
        "--mode", type=str, default="run", help="Optional mode flag (debug/run)."
    )
    # Multi‑seed / experimental arguments (used by the full experiment command)
    parser.add_argument(
        "--seeds",
        type=str,
        default=None,
        help="Comma‑separated list of seeds for multi‑seed runs.",
    )
    parser.add_argument(
        "--ratio",
        type=str,
        default=None,
        help="Wake‑to‑dream ratio as 'W:D' (e.g., '4:1').",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=None,
        help="Number of warm‑up steps before the first dream phase.",
    )
    parser.add_argument(
        "--glue-subset",
        type=str,
        default="mrpc",
        help="GLUE subset to use for training (default: mrpc).",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Configuration & reproducibility
    # ------------------------------------------------------------------
    torch.manual_seed(args.seed)
    config = Config()
    logger = get_logger(__name__, config=config, log_to_file=False)

    # Apply optional multi‑seed / experimental overrides
    if args.ratio:
        config.dream_ratio = parse_ratio(args.ratio)
        logger.info(f"Overriding dream_ratio to {config.dream_ratio}")
    if args.warmup is not None:
        config.warm_up_steps = args.warmup
        logger.info(f"Overriding warm_up_steps to {config.warm_up_steps}")

    # ------------------------------------------------------------------
    # Model and tokenizer
    # ------------------------------------------------------------------
    tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")
    model = DistilBertForMaskedLM.from_pretrained("distilbert-base-uncased")
    device = torch.device("cpu")
    model.to(device)

    # ------------------------------------------------------------------
    # Data loader (real GLUE data)
    # ------------------------------------------------------------------
    dataloader = build_dataloader(
        subset_name=args.glue_subset,
        tokenizer=tokenizer,
        batch_size=4,
        max_samples=200,  # small enough for quick CI runs
    )

    # ------------------------------------------------------------------
    # Helper to run a single training configuration
    # ------------------------------------------------------------------
    def run_one(seed: int) -> Tuple[int, Path]:
        torch.manual_seed(seed)
        trainer = Trainer(model=model, config=config, device=device)
        logger.info(f"Starting training for seed {seed} (max_steps={args.steps})")
        metrics = trainer.run_training_loop(dataloader, max_steps=args.steps)

        # Save checkpoint
        ckpt_path = Path("data/checkpoints") / f"checkpoint_seed_{seed}_step_{len(metrics)}.pt"
        save_checkpoint(model, ckpt_path)
        logger.info(f"Checkpoint saved to {ckpt_path}")

        # Write a tiny JSON summary
        summary_path = Path("data/results") / f"training_summary_seed_{seed}.json"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary = {
            "seed": seed,
            "steps_completed": len(metrics),
            "final_loss": metrics[-1]["loss"] if metrics else None,
            "checkpoint": str(ckpt_path),
        }
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Training summary written to {summary_path}")

        return len(metrics), summary_path

    # ------------------------------------------------------------------
    # Execution path: single‑seed (quickstart) vs. multi‑seed (full run)
    # ------------------------------------------------------------------
    if args.seeds:
        seeds = [int(s) for s in args.seeds.split(",") if s.strip()]
        for s in seeds:
            run_one(s)
    else:
        run_one(args.seed)

    logger.info("All requested training runs completed.")

if __name__ == "__main__":
    main()
