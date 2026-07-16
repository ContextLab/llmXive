"""
Environment configuration management for llmXive project.

This module provides:
- Path constants for the project structure
- Random seed pinning for reproducibility
- Environment variable management
- Configuration validation
"""

import os
import random
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

import numpy as np

from utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class ProjectPaths:
    """Immutable container for all project paths."""
    root: Path
    code: Path
    data: Path
    data_raw: Path
    data_processed: Path
    data_figures: Path
    tests: Path
    utils: Path
    models: Path
    features: Path
    specs: Path
    contracts: Path
    results: Path
    state: Path
    archive: Path

    def __post_init__(self):
        # Ensure all paths exist
        for path_attr in [
            'code', 'data', 'data_raw', 'data_processed', 'data_figures',
            'tests', 'utils', 'models', 'features', 'specs', 'contracts',
            'results', 'state', 'archive'
        ]:
            path = getattr(self, path_attr)
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured directory exists: {path}")

@dataclass
class RunConfig:
    """Configuration for a single run, including seeds and parameters."""
    seed: int
    sample_size: Optional[int] = None
    stratify_columns: list = field(default_factory=list)
    use_streaming: bool = True
    cpu_only: bool = True
    batch_size: int = 32
    n_folds: int = 5
    n_permutation_iterations: int = 1000
    alpha: float = 0.05
    dataset_name: str = "pick-a-pic"
    dataset_split: str = "train"
    clip_model_name: str = "openai/clip-vit-base-patch32"
    bert_model_name: str = "bert-base-uncased"
    spacy_model: str = "en_core_web_sm"

    def validate(self) -> None:
        """Validate configuration parameters."""
        if self.seed < 0:
            raise ValueError(f"Seed must be non-negative, got {self.seed}")
        if self.sample_size is not None and self.sample_size <= 0:
            raise ValueError(f"Sample size must be positive, got {self.sample_size}")
        if self.batch_size <= 0:
            raise ValueError(f"Batch size must be positive, got {self.batch_size}")
        if self.n_folds <= 1:
            raise ValueError(f"Number of folds must be > 1, got {self.n_folds}")
        if self.n_permutation_iterations <= 0:
            raise ValueError(f"Permutation iterations must be positive, got {self.n_permutation_iterations}")
        if not 0 < self.alpha < 1:
            raise ValueError(f"Alpha must be in (0, 1), got {self.alpha}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "seed": self.seed,
            "sample_size": self.sample_size,
            "stratify_columns": self.stratify_columns,
            "use_streaming": self.use_streaming,
            "cpu_only": self.cpu_only,
            "batch_size": self.batch_size,
            "n_folds": self.n_folds,
            "n_permutation_iterations": self.n_permutation_iterations,
            "alpha": self.alpha,
            "dataset_name": self.dataset_name,
            "dataset_split": self.dataset_split,
            "clip_model_name": self.clip_model_name,
            "bert_model_name": self.bert_model_name,
            "spacy_model": self.spacy_model
        }

class SeedManager:
    """Manages random seed pinning for reproducibility."""

    def __init__(self, seed: int):
        self.seed = seed
        self._set_seeds()
        logger.info(f"Random seed pinned to {seed}")

    def _set_seeds(self) -> None:
        """Set seeds for all random number generators."""
        random.seed(self.seed)
        np.random.seed(self.seed)
        # Note: torch seed is set where torch is imported if needed
        # We avoid importing torch here to keep config lightweight

    def get_state(self) -> Dict[str, int]:
        """Return current seed state for logging."""
        return {
            "python_random": random.getstate()[1][0] if hasattr(random.getstate()[1][0], '__int__') else random.getstate()[1][0],
            "numpy": np.random.get_state()[1][0]
        }

def get_project_root() -> Path:
    """Get the project root directory."""
    # Assuming this file is at code/config.py
    return Path(__file__).resolve().parent.parent

def get_paths() -> ProjectPaths:
    """Initialize and return project paths."""
    root = get_project_root()
    return ProjectPaths(
        root=root,
        code=root / "code",
        data=root / "data",
        data_raw=root / "data" / "raw",
        data_processed=root / "data" / "processed",
        data_figures=root / "data" / "figures",
        tests=root / "code" / "tests",
        utils=root / "code" / "utils",
        models=root / "code" / "models",
        features=root / "code" / "features",
        specs=root / "specs" / "001-llmxive-follow-up-extending-lens-rethink",
        contracts=root / "specs" / "001-llmxive-follow-up-extending-lens-rethink" / "contracts",
        results=root / "results",
        state=root / "state" / "projects" / "PROJ-925-llmxive-follow-up-extending-lens-rethink",
        archive=root / "archive"
    )

def get_config(seed: Optional[int] = None) -> RunConfig:
    """
    Get run configuration from environment or defaults.

    Args:
        seed: Optional seed override. If None, reads from LLMXIVE_SEED env var,
              or defaults to 42.

    Returns:
        Validated RunConfig instance.
    """
    if seed is None:
        seed = int(os.getenv("LLMXIVE_SEED", "42"))

    # Read optional parameters from environment
    sample_size = os.getenv("LLMXIVE_SAMPLE_SIZE")
    sample_size = int(sample_size) if sample_size else None

    stratify_str = os.getenv("LLMXIVE_STRATIFY_COLUMNS", "")
    stratify_columns = [col.strip() for col in stratify_str.split(",") if col.strip()]

    batch_size = os.getenv("LLMXIVE_BATCH_SIZE", "32")
    n_folds = os.getenv("LLMXIVE_N_FOLDS", "5")
    n_perm_iter = os.getenv("LLMXIVE_N_PERM_ITERATIONS", "1000")
    alpha = os.getenv("LLMXIVE_ALPHA", "0.05")

    config = RunConfig(
        seed=seed,
        sample_size=sample_size,
        stratify_columns=stratify_columns,
        batch_size=int(batch_size),
        n_folds=int(n_folds),
        n_permutation_iterations=int(n_perm_iter),
        alpha=float(alpha)
    )

    config.validate()
    return config

def init_run(seed: Optional[int] = None) -> tuple[RunConfig, SeedManager]:
    """
    Initialize a run with configuration and seed management.

    Args:
        seed: Optional seed override.

    Returns:
        Tuple of (RunConfig, SeedManager)
    """
    config = get_config(seed)
    seed_manager = SeedManager(config.seed)
    logger.info(f"Run initialized with seed {config.seed}")
    return config, seed_manager

# Global path instance for convenience
PATHS = get_paths()

if __name__ == "__main__":
    # Test configuration initialization
    paths = get_paths()
    print(f"Project root: {paths.root}")
    print(f"Data processed: {paths.data_processed}")
    print(f"Results: {paths.results}")

    config, seed_mgr = init_run(seed=42)
    print(f"Config seed: {config.seed}")
    print(f"Config sample_size: {config.sample_size}")
    print(f"Seed manager state: {seed_mgr.get_state()}")