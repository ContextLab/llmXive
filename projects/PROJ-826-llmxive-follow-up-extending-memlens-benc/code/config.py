"""
Configuration constants for the llmXive MemLens extension project.

This module centralizes all project-level hyperparameters and path settings
to ensure consistency across data loading, model inference, and evaluation.
"""

import os

# Project root is assumed to be the parent of the 'code' directory
# We use relative paths from the project root as specified in tasks.md
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Random seed for reproducibility across all libraries (torch, numpy, random)
SEED = 42

# Data paths relative to project root
DATA_PATH = os.path.join(_ROOT, 'data', 'raw')
OUTPUT_PATH = os.path.join(_ROOT, 'outputs')

# Hyperparameters
TOP_K = 5  # Number of retrieved context items for RAG
BATCH_SIZE = 4  # Batch size for inference (optimized for CPU memory constraints)

# Ensure output directories exist if not already created
# Note: T001 creates the structure, but this ensures safety on first run
os.makedirs(DATA_PATH, exist_ok=True)
os.makedirs(OUTPUT_PATH, exist_ok=True)