"""
Configuration module for the Dream-State Learning pipeline.

Handles hyperparameters, file paths, seed management, and enforces
CPU-only device execution as per project constraints.
"""

import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import torch


class Config:
    """
    Centralized configuration for the Dream-State Learning project.

    Attributes:
        project_root (Path): Absolute path to the project root.
        data_dir (Path): Base directory for data storage.
        raw_data_dir (Path): Directory for raw downloaded datasets.
        checkpoints_dir (Path): Directory for model checkpoints.
        results_dir (Path): Directory for output results and reports.
        logs_dir (Path): Directory for log files.

        # Hyperparameters
        seed (int): Global random seed for reproducibility.
        device (str): Computation device ('cpu' only enforced).
        max_wall_clock_hours (int): Maximum allowed runtime in hours.
        memory_limit_gb (int): Maximum allowed RAM in GB.

        # Training Hyperparameters
        learning_rate (float): Base learning rate.
        batch_size (int): Training batch size.
        max_steps (int): Maximum training steps.
        warmup_steps (int): Steps before dream phase begins (T016).
        dream_ratio (float): Ratio of dream steps to wake steps (e.g., 0.25 for 4:1).
        entropy_threshold (float): Minimum entropy threshold for batch validity (T017).
        max_entropy_retries (int): Max retries for low-entropy batches.

        # Model Hyperparameters
        model_name (str): Pre-trained model identifier (e.g., 'distilbert-base-uncased').
        max_seq_length (int): Maximum sequence length for inputs.
        mask_rate (float): Masking rate for DAE (T013).
        temperature (float): Temperature for sampling in dream phase.

        # Paths (Relative to project root)
        CONFIG_PATH = "code/config.py"
        LOGS_PATH = "data/logs"
        RESULTS_PATH = "data/results"
        CHECKPOINTS_PATH = "data/checkpoints"
        RAW_DATA_PATH = "data/raw"
        DATA_PATH = "data"
    """

    def __init__(self):
        self._project_root = Path(__file__).resolve().parent.parent
        self._seed = 42
        self._device = "cpu"  # Force CPU as per constraints

        # Enforce CPU-only device
        if torch.cuda.is_available():
            print(f"Warning: GPU detected but {self.__class__.__name__} enforces CPU-only mode.")

        # Hyperparameters
        self.learning_rate: float = 5e-5
        self.batch_size: int = 8
        self.max_steps: int = 1000
        self.warmup_steps: int = 10  # T016: Skip dream phase for first 10 steps
        self.dream_ratio: float = 0.25  # 1 dream step per 4 wake steps
        self.entropy_threshold: float = 0.5  # Bits (T017)
        self.max_entropy_retries: int = 3
        self.temperature: float = 0.9

        # Model settings
        self.model_name: str = "distilbert-base-uncased"
        self.max_seq_length: int = 128
        self.mask_rate: float = 0.15  # Standard BERT mask rate

        # Resource constraints
        self.max_wall_clock_hours: int = 5
        self.memory_limit_gb: int = 7

        # Set seeds
        self.set_seed(self._seed)

    @property
    def project_root(self) -> Path:
        return self._project_root

    @property
    def data_dir(self) -> Path:
        return self.project_root / self.DATA_PATH

    @property
    def raw_data_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def checkpoints_dir(self) -> Path:
        return self.data_dir / "checkpoints"

    @property
    def results_dir(self) -> Path:
        return self.data_dir / "results"

    @property
    def logs_dir(self) -> Path:
        return self.data_dir / "logs"

    @property
    def device(self) -> str:
        return self._device

    @property
    def seed(self) -> int:
        return self._seed

    def set_seed(self, seed: int) -> None:
        """
        Sets the random seed for reproducibility across all libraries.

        Args:
            seed (int): The seed value.
        """
        self._seed = seed
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

    def to_dict(self) -> Dict[str, Any]:
        """Returns a dictionary representation of the configuration."""
        return {
            "project_root": str(self.project_root),
            "seed": self.seed,
            "device": self.device,
            "learning_rate": self.learning_rate,
            "batch_size": self.batch_size,
            "max_steps": self.max_steps,
            "warmup_steps": self.warmup_steps,
            "dream_ratio": self.dream_ratio,
            "entropy_threshold": self.entropy_threshold,
            "max_entropy_retries": self.max_entropy_retries,
            "temperature": self.temperature,
            "model_name": self.model_name,
            "max_seq_length": self.max_seq_length,
            "mask_rate": self.mask_rate,
            "max_wall_clock_hours": self.max_wall_clock_hours,
            "memory_limit_gb": self.memory_limit_gb,
        }

    def ensure_directories(self) -> None:
        """Creates all necessary directories defined in the config."""
        dirs = [
            self.data_dir,
            self.raw_data_dir,
            self.checkpoints_dir,
            self.results_dir,
            self.logs_dir,
            self.project_root / "code" / "models" / "checkpoints",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)


# Singleton instance for easy import
config = Config()