"""
Training package for the Consciousness Bootstrapping project.
Contains training loops, dataset loaders, and training utilities.
"""
from .train import PileDataset, train_epoch, save_checkpoint, run_training, main

__all__ = [
    "PileDataset",
    "train_epoch",
    "save_checkpoint",
    "run_training",
    "main"
]
