"""
seed_config.py
----------------
Centralised seed configuration for the project.

Importing this module will set deterministic seeds for the
supported random‑number generators.  All other modules should import
``SEED`` from here if they need the numeric value.
"""

import random

import numpy as np

from llmxive_toolkit import get_logger

log = get_logger(__name__)

# The single source of truth for the project‑wide seed.
SEED = 20231027

# Apply the seed to the standard libraries.
random.seed(SEED)
np.random.seed(SEED)

try:
    import torch

    torch.manual_seed(SEED)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    log.debug("Torch seed set to %s", SEED)
except Exception as exc:  # pragma: no cover – torch optional
    log.debug("Torch not available; seed not set: %s", exc)
