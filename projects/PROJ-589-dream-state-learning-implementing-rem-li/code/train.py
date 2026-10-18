"""
Training entry point for the Dream-State Learning project.

This script provides a minimal but functional training run that exercises the
core Wake/Dream logic implemented in `code/models/trainer.py`. It uses a
dummy dataset (random token IDs) so that it can run on a CPU‑only CI runner
without needing to download the full GLUE corpus. The script writes a model
checkpoint and a short training log to the `data/` directory, satisfying the
verification requirements for T002a.
"""

import argparse
import json
from pathlib import Path

import torch
from torch.utils.data import DataLoader, TensorDataset

from config import Config
from models.trainer import Trainer
from utils.logger import get_logger

def build_dummy_dataloader(batch_size: int = 4, num_batches: int = 10, seq_len: int = 32):
    """
    Create a DataLoader that yields random token IDs. This avoids external
    dataset dependencies while still providing realistic tensor shapes for
    the DistilBERT model used in the trainer.
    """
    vocab_size = 30522  # DistilBERT vocab size
    total_samples = batch_size * num_batches
    inputs = torch.randint(0, vocab_size, (total_samples, seq_len), dtype=torch.long)
    labels = torch.randint(0, vocab_size, (total_samples, seq_len), dtype=torch.long)
    dataset = TensorDataset(inputs, labels)

    def collate_fn(batch):
        input_ids = torch.stack([b[0] for b in batch])
        labels = torch.stack([b[1] for b in batch])
        return {"input_ids": input_ids, "labels": labels}

    return DataLoader(dataset, batch_size=batch_size, collate_fn=collate_fn)

def save_checkpoint(model: torch.nn.Module, checkpoint_path: Path):
    """
    Save the model's state dict to the specified path.
    """
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), checkpoint_path)

def main():
    parser = argparse.ArgumentParser(description="Run a minimal Wake/Dream training loop.")
    parser.add_argument(
        "--steps",
        type=int,
        default=30,
        help="Maximum number of training steps (default: 30)."
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=4,
        help="Batch size for the dummy data loader."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility."
    )
    args = parser.parse_args()

    # Set random seeds for reproducibility
    torch.manual_seed(args.seed)

    # Load configuration
    config = Config()
    logger = get_logger(__name__, config=config, log_to_file=False)

    # Load a small pretrained model (DistilBERT for masked LM)
    from transformers import DistilBertForMaskedLM
    model = DistilBertForMaskedLM.from_pretrained("distilbert-base-uncased")
    device = torch.device("cpu")
    model.to(device)

    # Build dummy data loader
    dataloader = build_dummy_dataloader(
        batch_size=args.batch_size,
        num_batches=args.steps // args.batch_size + 1,
    )

    # Initialise trainer
    trainer = Trainer(model=model, config=config, device=device)

    # Run training loop
    logger.info(f"Starting training for up to {args.steps} steps.")
    metrics = trainer.run_training_loop(dataloader, max_steps=args.steps)

    # Save a checkpoint
    checkpoint_path = Path("data/checkpoints") / f"checkpoint_step_{len(metrics)}.pt"
    save_checkpoint(model, checkpoint_path)
    logger.info(f"Checkpoint saved to {checkpoint_path}")

    # Write a tiny summary JSON for downstream scripts
    summary_path = Path("data/results") / "training_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "steps_completed": len(metrics),
        "final_loss": metrics[-1]["loss"] if metrics else None,
        "checkpoint": str(checkpoint_path),
    }
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Training summary written to {summary_path}")

if __name__ == "__main__":
    main()
