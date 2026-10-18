"""
Training entry point for the Dream-State Learning project.

This script implements the core Wake/Dream training loop using a real
GLUE subset (MRPC by default). It supports both single‑seed debug runs
and multi‑seed experiments. All data is fetched from the HuggingFace
``datasets`` library, ensuring that the script operates on genuine
data rather than synthetic placeholders.

The script writes:
  * a model checkpoint to ``data/checkpoints/``
  * a concise JSON summary to ``data/results/``

These outputs satisfy the quick‑start verification steps.
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


def parse_ratio(ratio_str: str) -> int:
    """
    Convert a ``W:D`` ratio string into the integer ``W + D`` expected by
    :class:`DreamScheduler`.  Example: ``4:1`` → ``5``.
    """
    try:
        w, d = ratio_str.split(":")
        return int(w) + int(d)
    except Exception as exc:
        raise ValueError(
            f"Invalid ratio format '{ratio_str}'. Expected 'W:D' (e.g., '4:1')."
        ) from exc


def build_dataloader(
    subset_name: str,
    tokenizer: DistilBertTokenizerFast,
    batch_size: int = 4,
    max_samples: int = 200,
) -> DataLoader:
    """
    Load a GLUE subset, tokenize it, and return a ``DataLoader`` that yields
    ``input_ids`` and ``labels`` tensors suitable for masked‑language‑model
    training.

    Only ``max_samples`` examples are used so that the script finishes
    quickly on a CPU‑only runner.
    """
    # Load the GLUE subset directly via the ``datasets`` library.
    # This avoids any custom loader that may have integrity‑checking bugs.
    glue = load_dataset("glue", subset_name, split="train")
    glue = glue.select(range(min(max_samples, len(glue))))  # truncate safely

    # Concatenate the two sentences (MRPC) or fall back to a single field.
    sentences: List[str] = []
    for record in glue:
        if "sentence1" in record and "sentence2" in record:
            sentences.append(f"{record['sentence1']} {record['sentence2']}")
        elif "sentence" in record:
            sentences.append(record["sentence"])
        else:
            # As a last resort, stringify the whole record.
            sentences.append(str(record))

    tokenized = tokenizer(
        sentences,
        padding="max_length",
        truncation=True,
        max_length=64,
        return_tensors="pt",
    )
    input_ids = tokenized["input_ids"]
    # For the DAE objective the target is the original input ids.
    labels = input_ids.clone()

    dataset = TensorDataset(input_ids, labels)

    def collate_fn(batch: Tuple[torch.Tensor, torch.Tensor]):
        input_ids_batch = torch.stack([b[0] for b in batch])
        labels_batch = torch.stack([b[1] for b in batch])
        return {"input_ids": input_ids_batch, "labels": labels_batch}

    return DataLoader(dataset, batch_size=batch_size, collate_fn=collate_fn)


def save_checkpoint(model: torch.nn.Module, checkpoint_path: Path):
    """
    Persist the model's state dict.  Parent directories are created
    automatically.
    """
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), checkpoint_path)


def main():
    parser = argparse.ArgumentParser(
        description="Run the Wake/Dream training loop on a real GLUE subset."
    )
    # Single‑seed arguments (used by the quick‑start debug command)
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

    # Apply optional overrides for experiments
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
        max_samples=200,
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
    # Execution path: single‑seed (quick‑start) vs. multi‑seed (full run)
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
