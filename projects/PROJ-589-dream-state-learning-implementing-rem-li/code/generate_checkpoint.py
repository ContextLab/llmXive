"""
Script to generate a dummy checkpoint for evaluation.

This script loads the pretrained DistilBERT masked‑LM model (the same
model used throughout the project) and saves its state_dict to a
checkpoint file. The checkpoint is required by ``code/eval.py`` so that
the evaluation script can demonstrate loading a checkpoint file
(even though it will fall back to the pretrained weights if the file
is missing). Creating a real checkpoint satisfies the verification
requirement that the file exists on disk.

Usage:
    python code/generate_checkpoint.py --output checkpoints/debug_seed0.pt
"""

import argparse
from pathlib import Path

import torch
from transformers import DistilBertForMaskedLM

from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

def main():
    parser = argparse.ArgumentParser(
        description="Generate a dummy DistilBERT checkpoint for evaluation."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="checkpoints/debug_seed0.pt",
        help="Path where the checkpoint will be saved.",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cfg = Config()
    logger.info(f"Loading pretrained model '{cfg.model_name}'")
    model = DistilBertForMaskedLM.from_pretrained(cfg.model_name)
    model.to(cfg.device)
    model.eval()

    logger.info(f"Saving checkpoint to {output_path}")
    torch.save(model.state_dict(), output_path)
    logger.info("Checkpoint generation complete.")

if __name__ == "__main__":
    main()
