"""
Configuration module for Dream-State Learning.
This file defines a Config class used throughout the project and also provides
a lightweight ``get_config`` helper used by the unit‑tests for T002a.
The implementation is self‑contained and does not rely on any external
configuration files.
"""

import os
import random
from pathlib import Path
from typing import Any

import numpy as np
import torch
import psutil

# ----------------------------------------------------------------------
# Public constant for verification (required by task T001)
# ----------------------------------------------------------------------
# The verification script checks for this exact attribute.
MAX_MEMORY_MB = 6300

class Config:
    """
    Central configuration container.
    All hyper‑parameters and runtime limits are defined here.
    """
    def __init__(self):
        # Core training hyper‑parameters
        self.device = torch.device('cpu')
        self.learning_rate = 5e-5
        self.dream_ratio = 5                # wake‑to‑dream steps (default 5 wake steps per dream)
        self.warm_up_steps = 20             # exact warm‑up period required by the spec
        self.perplexity_skip_threshold = 50.0
        self.mask_rate = 0.15
        self.kd_temperature = 1.0
        self.kd_alpha = 0.5
        self.max_retries = 3
        self.entropy_threshold = 0.5
        self.held_out_subset = None
        self.held_out_batch_size = 8
        
        # Model and Path configuration
        # Use a tiny DistilBERT variant to keep downloads fast in the quick‑start.
        self.model_name = "sshleifer/tiny-distilbert-base-uncased"
        self.log_dir = "data/logs"
        self.results_dir = "data/results"
        self.checkpoint_dir = "data/checkpoints"

        # Enforce CPU‑only execution
        self._enforce_cpu_only()

        # Enforce memory limit (6.3 GB)
        self.memory_limit_bytes = int(6.3 * 1024 ** 3)  # 6.3 GB in bytes
        self._enforce_memory_limit()

    def get(self, key: str, default: Any = None) -> Any:
        """Dictionary‑style accessor used throughout the code base."""
        return getattr(self, key, default)

    # ------------------------------------------------------------------
    # Helper methods for the task
    # ------------------------------------------------------------------
    def _enforce_cpu_only(self):
        """
        Force CPU execution even if CUDA devices are present.
        """
        if torch.cuda.is_available():
            self.device = torch.device('cpu')
            # Lightweight warning – avoids pulling in the full logger at import time
            print("[Config] CUDA detected; forcing CPU‑only execution.")

    def _enforce_memory_limit(self):
        """
        Abort early if the current process exceeds the allowed RSS.
        """
        process = psutil.Process()
        rss = process.memory_info().rss
        if rss > self.memory_limit_bytes:
            raise MemoryError(
                f"Memory usage {rss / (1024 ** 3):.2f} GB exceeds the allowed limit of 6.3 GB."
            )

# ----------------------------------------------------------------------
# Helper for unit‑tests (T002a)
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
        device=torch.device('cpu'),
        # Tiny model for fast downloads in tests / quick‑start
        model_name="sshleifer/tiny-distilbert-base-uncased",
        log_dir="data/logs",
        results_dir="data/results",
        checkpoint_dir="data/checkpoints",
        # Add the missing memory limit attribute required by Trainer
        memory_limit_bytes=int(6.3 * 1024 ** 3)
    )
    # Provide a ``get`` method like the real Config class
    def _get(attr, default=None):
        return getattr(cfg, attr, default)
    cfg.get = _get
    return cfg