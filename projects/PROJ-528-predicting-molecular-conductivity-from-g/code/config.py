"""
Central configuration constants used throughout the pipeline.
"""

from pathlib import Path

# Base data directory (managed by llmxive_toolkit)
from llmxive_toolkit import paths

# Resolve the absolute data root – this is used by many modules.
DATA_PATH = str(paths.data())

# Random seed for reproducibility
SEED = 42

# Sensitivity analysis outlier thresholds (σ multiples)
SENSITIVITY_THRESHOLDS = [2.5, 3.0, 3.5]
