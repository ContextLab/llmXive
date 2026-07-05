"""
llmXive Project: Evaluating the Impact of Outlier Removal Methods on Variance Estimation.

This package provides the core infrastructure for data generation, outlier removal,
metrics calculation, and statistical analysis.

Global Configuration:
  - Random Seed: Fixed to 42 for reproducibility across all experiments.
"""

import random
import os

# Ensure reproducibility for all random operations
# This satisfies the requirement for a global random seed configuration.
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# Optional: Set numpy seed if numpy is available (imported lazily in data generation)
# This is done here to ensure global consistency if numpy is used anywhere in the package.
try:
    import numpy as np
    np.random.seed(RANDOM_SEED)
except ImportError:
    pass

# Expose the seed constant for other modules
__all__ = ['RANDOM_SEED']