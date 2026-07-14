from __future__ import annotations

import os
from pathlib import Path
from typing import List
import joblib

# Avoid circular imports by importing only when needed
# DO NOT import train_gnn here at module level


def save_gnn_checkpoint(model, seed: int, checkpoint_dir: Path = None) -> Path:
    """Save a GNN model checkpoint."""
    if checkpoint_dir is None:
        checkpoint_dir = Path(__file__).parent.parent / "data" / "checkpoints"

    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = checkpoint_dir / f"model_seed_{seed}.pt"

    # For GNN models, save as torch format
    import torch
    torch.save({
        'model_state_dict': model.state_dict(),
        'seed': seed
    }, checkpoint_path)

    return checkpoint_path


def save_rf_checkpoint(model, seed: int, checkpoint_dir: Path = None) -> Path:
    """Save a Random Forest model checkpoint."""
    if checkpoint_dir is None:
        checkpoint_dir = Path(__file__).parent.parent / "data" / "checkpoints"

    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = checkpoint_dir / f"rf_seed_{seed}.pkl"

    # For Random Forest, save as joblib/pkl
    joblib.dump(model, checkpoint_path)

    return checkpoint_path


def main() -> None:
    """Main entry point - used for checkpoint operations."""
    print("Checkpoint saving utilities - call save_gnn_checkpoint or save_rf_checkpoint directly")


if __name__ == '__main__':
    main()
