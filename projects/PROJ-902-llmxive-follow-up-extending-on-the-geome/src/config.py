"""
Configuration module for the llmXive geometry extension project.

This module defines:
- Seed lists for mask derivation and evaluation.
- Global hyper‑parameters used throughout training scripts.
The values are deliberately simple but respect the constraints required by
the contract tests (e.g., learning rate in (0, 1], positive batch size, etc.).
"""

# ----------------------------------------------------------------------
# Seed configuration
# ----------------------------------------------------------------------
# Seeds used to derive masks for the OPD baseline. The exact number is not
# critical for the contract test – it only checks that the list is non‑empty
# and that it is disjoint from `EVAL_SEEDS`.
MASK_DERIVATION_SEEDS = list(range(0, 5))

# Seeds used for evaluation runs. Chosen to be disjoint from the mask‑derivation
# seeds and to provide a small but non‑trivial set of reproducible runs.
EVAL_SEEDS = list(range(100, 105))

# ----------------------------------------------------------------------
# Global hyper‑parameters
# ----------------------------------------------------------------------
# Learning rate for optimizer – must be a float in (0, 1].
LEARNING_RATE = 0.01

# Batch size for training – must be a positive integer.
BATCH_SIZE = 32

# Number of epochs for training – must be a positive integer.
EPOCHS = 3

# Additional hyper‑parameters can be added here as the project evolves.