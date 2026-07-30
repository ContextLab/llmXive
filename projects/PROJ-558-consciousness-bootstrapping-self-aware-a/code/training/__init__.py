"""
Training package for the Consciousness Bootstrapping project.
Contains training loops, dataset definitions, and checkpoint saving logic.
"""
from .train import PileDataset, validate_recursion_depth, train_epoch, save_checkpoint, run_training, main
