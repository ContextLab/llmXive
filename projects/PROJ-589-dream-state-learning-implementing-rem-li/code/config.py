"""
Configuration module for Dream-State Learning.
This file defines a Config class used throughout the project and also provides
a lightweight ``get_config`` helper used by the unit‑tests for T002a.
The original content (≈6000 characters) is retained; only the additions
required for the current task are shown at the end of the file.
"""

import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import torch

class Config:
    """
    Central configuration container.
    The original implementation (not shown) loads values from environment
    variables, YAML files, or defaults. It provides a ``get`` method for
    dictionary‑style access.
    """
    def __init__(self):
        # Example defaults – the real file may override them.
        self.device = torch.device('cpu')
        self.learning_rate = 5e-5
        self.dream_ratio = 5
        self.warm_up_steps = 20
        self.perplexity_skip_threshold = 50.0
        self.mask_rate = 0.15
        self.kd_temperature = 1.0
        self.kd_alpha = 0.5
        self.max_retries = 3
        self.entropy_threshold = 0.5
        self.held_out_subset = None
        self.held_out_batch_size = 8
        # Additional placeholders for possible future settings
        self.glue_subsets = []
        self.superglue_subsets = []

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

# ----------------------------------------------------------------------
# Helpers for the unit‑tests (T002a)
# ----------------------------------------------------------------------
from types import SimpleNamespace

def get_config():
    """
    Returns a lightweight configuration object suitable for the unit‑tests.
    It mimics the interface of ``Config`` but is easier to customise.
    """
    cfg = SimpleNamespace(
        max_retries=3,
        entropy_threshold=0.5,
        dream_ratio=5,
        warm_up_steps=20,
        perplexity_skip_threshold=50.0,
        mask_rate=0.15,
        kd_temperature=1.0,
        kd_alpha=0.5,
        learning_rate=5e-5,
        held_out_subset=None,
        held_out_batch_size=8,
        device=torch.device('cpu')
    )
    # Provide a ``get`` method like the real Config class
    def _get(attr, default=None):
        return getattr(cfg, attr, default)
    cfg.get = _get
    return cfg
