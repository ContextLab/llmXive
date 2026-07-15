"""
Experiment configuration manager for llmXive pipeline.

This module provides centralized configuration for experiments, including
random seeds, evaluation cutoffs, and other hyperparameters required for
reproducible research.
"""

import os
import random
from typing import List, Set, Dict, Any, Optional

import numpy as np
import torch

# ============================================================================
# SPEC COMPLIANCE: FR-007
# The CUTOFFS constant MUST be initialized to the specific set {0.01, 0.05, 0.1}
# ============================================================================
CUTOFFS: Set[float] = {0.01, 0.05, 0.1}

# Default random seed for reproducibility
DEFAULT_SEED: int = 42

# Project root directory (relative to where scripts are run)
PROJECT_ROOT: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Data directories
DATA_RAW_DIR: str = os.path.join(PROJECT_ROOT, "data", "raw")
DATA_FLOW_DIR: str = os.path.join(PROJECT_ROOT, "data", "flow")
DATA_METRICS_DIR: str = os.path.join(PROJECT_ROOT, "data", "metrics")
RESULTS_DIR: str = os.path.join(PROJECT_ROOT, "results")

# Ensure directories exist
def ensure_directories() -> None:
    """Create all required data directories if they do not exist."""
    for dir_path in [DATA_RAW_DIR, DATA_FLOW_DIR, DATA_METRICS_DIR, RESULTS_DIR]:
        os.makedirs(dir_path, exist_ok=True)


class ExperimentConfig:
    """
    Centralized configuration manager for experiment parameters.

    This class encapsulates all hyperparameters and settings required for
    running experiments, ensuring consistency across the pipeline.
    """

    def __init__(
        self,
        seed: int = DEFAULT_SEED,
        device: str = "cpu",
        batch_size: int = 1,
        num_clips: int = 50,
        flow_model: str = "raft-small",
        cutoffs: Optional[Set[float]] = None,
    ):
        """
        Initialize experiment configuration.

        Args:
            seed: Random seed for reproducibility.
            device: Compute device ('cpu' or 'cuda').
            batch_size: Batch size for inference.
            num_clips: Number of clips to process in the experiment.
            flow_model: Optical flow model to use (e.g., 'raft-small', 'farneback').
            cutoffs: Set of flow magnitude cutoffs for analysis. Defaults to CUTOFFS.
        """
        self.seed = seed
        self.device = device
        self.batch_size = batch_size
        self.num_clips = num_clips
        self.flow_model = flow_model
        self.cutoffs = cutoffs if cutoffs is not None else CUTOFFS

        # Validate configuration
        self._validate()

        # Initialize random seeds
        self._set_seeds()

    def _validate(self) -> None:
        """Validate configuration parameters."""
        if self.seed < 0:
            raise ValueError(f"Seed must be non-negative, got {self.seed}")
        if self.batch_size < 1:
            raise ValueError(f"Batch size must be at least 1, got {self.batch_size}")
        if self.num_clips < 1:
            raise ValueError(f"Number of clips must be at least 1, got {self.num_clips}")
        if not isinstance(self.cutoffs, set) or len(self.cutoffs) == 0:
            raise ValueError(f"Cutoffs must be a non-empty set, got {self.cutoffs}")
        if self.device not in ["cpu", "cuda"]:
            raise ValueError(f"Device must be 'cpu' or 'cuda', got {self.device}")

    def _set_seeds(self) -> None:
        """Set random seeds for reproducibility across libraries."""
        random.seed(self.seed)
        np.random.seed(self.seed)
        torch.manual_seed(self.seed)
        if self.device == "cuda" and torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.seed)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to a dictionary.

        Returns:
            Dictionary representation of the configuration.
        """
        return {
            "seed": self.seed,
            "device": self.device,
            "batch_size": self.batch_size,
            "num_clips": self.num_clips,
            "flow_model": self.flow_model,
            "cutoffs": sorted(list(self.cutoffs)),
        }

    def __repr__(self) -> str:
        """String representation of the configuration."""
        return f"ExperimentConfig(seed={self.seed}, device={self.device}, cutoffs={sorted(self.cutoffs)})"


def get_default_config() -> ExperimentConfig:
    """
    Get a default experiment configuration.

    Returns:
        ExperimentConfig with default parameters.
    """
    return ExperimentConfig()


# Convenience function to ensure directories exist on import
ensure_directories()
