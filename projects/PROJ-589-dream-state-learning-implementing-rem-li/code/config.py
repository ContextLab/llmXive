"""
Configuration module for Dream-State Learning project.

Contains hyperparameters, paths, seed management, and device settings.
Enforces CPU-only execution and the 6.3 GB memory budget (FR-005).
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import torch


class Config:
    """
    Central configuration class for the Dream-State Learning pipeline.

    Handles all hyperparameters, file paths, and runtime settings.
    """

    # --- Hyperparameters ---
    # Masking rate for DAE (Dream phase), BERT-standard 15%
    MASK_RATE: float = 0.15

    # Training parameters
    BATCH_SIZE: int = 8
    LEARNING_RATE: float = 5e-5
    NUM_EPOCHS: int = 3
    MAX_GRAD_NORM: float = 1.0

    # Dream phase scheduling (FR-007: exactly 20 wake-only warm-up steps;
    # FR-001: 4:1 wake-to-dream ratio per US-1 acceptance scenario)
    WARMUP_STEPS: int = 20
    WAKE_TO_DREAM_RATIO: int = 4

    # Entropy check parameters (edge case: retry up to 3 times)
    MIN_ENTROPY_THRESHOLD: float = 0.5  # bits per token
    MAX_ENTROPY_RETRIES: int = 3

    # Perplexity gate for dream-phase skipping (edge case: skip if > 50)
    MAX_DREAM_PERPLEXITY: float = 50.0

    # Temperature sweep for sensitivity analysis (FR-006)
    TEMPERATURES: List[float] = [0.5, 1.0, 1.5, 2.0]
    DEFAULT_TEMPERATURE: float = 1.0

    # Statistical analysis
    SIGNIFICANCE_LEVEL: float = 0.05
    NUM_SEEDS: int = 5

    # Resource limits (FR-005 / US-3: peak RSS must stay below 6.3 GB
    # within the 7 GB GitHub Actions runner limit; wall clock < 5 hours)
    MAX_WALL_CLOCK_HOURS: float = 5.0
    MAX_MEMORY_GB: float = 6.3

    # Model architecture (fixed per plan: DistilBERT-base-uncased)
    MODEL_NAME: str = "distilbert-base-uncased"

    # Datasets used by the pipeline (consumed by code/data_loader.py)
    glue_subsets: List[str] = ["mnli", "qnli"]
    superglue_subsets: List[str] = []

    # --- Paths ---
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    DATA_DIR: Path = PROJECT_ROOT / "data"
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    CHECKPOINTS_DIR: Path = DATA_DIR / "checkpoints"
    RESULTS_DIR: Path = DATA_DIR / "results"
    LOGS_DIR: Path = DATA_DIR / "logs"
    TESTS_DIR: Path = PROJECT_ROOT / "tests"

    # --- Device Configuration ---
    # Enforce CPU-only for CI compatibility. CUDA is never used unless the
    # operator explicitly opts in via DREAM_STATE_ALLOW_GPU=true.
    DEVICE: str = "cpu"
    if torch.cuda.is_available():
        if os.environ.get("DREAM_STATE_ALLOW_GPU", "false").lower() == "true":
            DEVICE = "cuda"

    # --- Seed Management ---
    DEFAULT_SEED: int = 42

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize configuration with optional seed override.

        Args:
            seed: Random seed for reproducibility. If None, uses DEFAULT_SEED.
        """
        self.seed = seed if seed is not None else self.DEFAULT_SEED
        self._set_seeds(self.seed)

        # Ensure directories exist
        self._ensure_directories()

    @property
    def log_dir(self) -> Path:
        """Directory where structured JSON logs are written."""
        return self.LOGS_DIR

    def _set_seeds(self, seed: int) -> None:
        """Set all random seeds for reproducibility."""
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

    def _ensure_directories(self) -> None:
        """Create required directory structure if it doesn't exist."""
        dirs = [
            self.DATA_DIR,
            self.RAW_DATA_DIR,
            self.PROCESSED_DATA_DIR,
            self.CHECKPOINTS_DIR,
            self.RESULTS_DIR,
            self.LOGS_DIR,
            self.TESTS_DIR,
        ]

        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Dictionary-style accessor so callers can do config.get(key, default).

        Args:
            key: Attribute name to look up.
            default: Value returned if the attribute does not exist.

        Returns:
            The attribute value or the default.
        """
        return getattr(self, key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration to a dictionary."""
        return {
            "mask_rate": self.MASK_RATE,
            "batch_size": self.BATCH_SIZE,
            "learning_rate": self.LEARNING_RATE,
            "num_epochs": self.NUM_EPOCHS,
            "max_grad_norm": self.MAX_GRAD_NORM,
            "warmup_steps": self.WARMUP_STEPS,
            "wake_to_dream_ratio": self.WAKE_TO_DREAM_RATIO,
            "min_entropy_threshold": self.MIN_ENTROPY_THRESHOLD,
            "max_entropy_retries": self.MAX_ENTROPY_RETRIES,
            "max_dream_perplexity": self.MAX_DREAM_PERPLEXITY,
            "temperatures": self.TEMPERATURES,
            "default_temperature": self.DEFAULT_TEMPERATURE,
            "significance_level": self.SIGNIFICANCE_LEVEL,
            "num_seeds": self.NUM_SEEDS,
            "max_wall_clock_hours": self.MAX_WALL_CLOCK_HOURS,
            "max_memory_gb": self.MAX_MEMORY_GB,
            "model_name": self.MODEL_NAME,
            "device": self.DEVICE,
            "seed": self.seed,
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """
        Create a Config instance from a dictionary.

        Args:
            config_dict: Dictionary containing configuration values.

        Returns:
            Config instance with values from the dictionary.
        """
        config = cls()

        for key, value in config_dict.items():
            if hasattr(config, key):
                setattr(config, key, value)

        return config
