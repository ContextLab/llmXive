"""
Configuration management and seed pinning for the llmXive psychology research pipeline.

This module provides:
- Global configuration state (paths, logging levels, data sources)
- Reproducibility seed management (random seeds for numpy, random, torch if available)
- Environment variable overrides
"""

import os
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, List

# Attempt to import numpy and torch for seed setting if available
# These are optional dependencies for reproducibility
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None  # type: ignore

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    torch = None  # type: ignore

# Import logging utility from sibling module
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ProjectConfig:
    """
    Central configuration object for the research pipeline.

    Attributes:
        project_root: Absolute path to the project root directory.
        data_root: Absolute path to the data directory.
        code_root: Absolute path to the code directory.
        output_root: Absolute path to the processed data/figures directory.
        seed: Global random seed for reproducibility.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR).
        data_sources: List of allowed data source URLs or paths.
        allow_external_download: Whether to allow downloading data from external sources.
    """
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent)
    data_root: Path = field(init=False)
    code_root: Path = field(init=False)
    output_root: Path = field(init=False)
    seed: int = 42
    log_level: str = "INFO"
    data_sources: List[str] = field(default_factory=lambda: [
        "https://clinicaltrials.gov",
        "https://osf.io"
    ])
    allow_external_download: bool = True

    def __post_init__(self):
        """Resolve absolute paths after initialization."""
        # Ensure project_root is absolute
        if not self.project_root.is_absolute():
            self.project_root = self.project_root.resolve()

        # Define derived paths relative to project_root
        self.data_root = self.project_root / "data"
        self.code_root = self.project_root / "code"
        self.output_root = self.project_root / "data" / "processed"

        # Ensure directories exist
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create necessary directory structure if it doesn't exist."""
        dirs_to_create = [
            self.data_root,
            self.data_root / "raw",
            self.data_root / "processed",
            self.data_root / "figures",
            self.code_root,
            self.project_root / "tests",
            self.project_root / "contracts",
            self.project_root / "docs",
            self.project_root / "specs"
        ]
        for d in dirs_to_create:
            d.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {d}")

    def validate(self) -> bool:
        """
        Validate the configuration.

        Returns:
            True if configuration is valid, False otherwise.
        """
        if not self.project_root.exists():
            logger.error(f"Project root does not exist: {self.project_root}")
            return False

        if not self.data_root.exists():
            logger.error(f"Data root does not exist: {self.data_root}")
            return False

        if not (0 <= self.seed <= 2**32 - 1):
            logger.error(f"Seed out of valid range: {self.seed}")
            return False

        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            logger.error(f"Invalid log level: {self.log_level}")
            return False

        logger.info("Configuration validation passed.")
        return True


# Global configuration instance
_config: Optional[ProjectConfig] = None


def get_config() -> ProjectConfig:
    """
    Get the global configuration instance.

    If not initialized, creates a new instance with defaults or environment overrides.

    Returns:
        The global ProjectConfig instance.
    """
    global _config
    if _config is None:
        _config = _load_config_from_env()
    return _config


def _load_config_from_env() -> ProjectConfig:
    """
    Load configuration from environment variables or defaults.

    Environment variables:
        PROJ_ROOT: Override project root directory.
        DATA_SEED: Override random seed.
        LOG_LEVEL: Override logging level.
        ALLOW_DOWNLOAD: Override external download permission (true/false).
    """
    # Get project root from environment or default
    root_env = os.getenv("PROJ_ROOT")
    if root_env:
        root = Path(root_env)
    else:
        # Default to parent of utils directory (project root)
        root = Path(__file__).resolve().parent.parent.parent

    # Get seed from environment
    seed_env = os.getenv("DATA_SEED")
    seed = int(seed_env) if seed_env else 42

    # Get log level from environment
    log_level_env = os.getenv("LOG_LEVEL", "INFO")

    # Get download permission from environment
    allow_download_env = os.getenv("ALLOW_DOWNLOAD", "true").lower()
    allow_download = allow_download_env in ("true", "1", "yes")

    config = ProjectConfig(
        project_root=root,
        seed=seed,
        log_level=log_level_env,
        allow_external_download=allow_download
    )

    # Validate before returning
    if not config.validate():
        logger.warning("Configuration validation failed, proceeding with defaults.")

    logger.info(f"Loaded configuration: root={config.project_root}, seed={config.seed}")
    return config


def set_seed(seed: Optional[int] = None) -> None:
    """
    Set the global random seed for reproducibility.

    This function sets seeds for:
    - Python's random module
    - NumPy (if available)
    - PyTorch (if available)

    Args:
        seed: The seed value. If None, uses the global config seed.
    """
    if seed is None:
        seed = get_config().seed

    logger.info(f"Setting global random seed to {seed}")

    # Python random
    random.seed(seed)

    # NumPy
    if HAS_NUMPY and np is not None:
        np.random.seed(seed)

    # PyTorch
    if HAS_TORCH and torch is not None:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

    logger.debug("Seed set successfully for all available libraries.")


def get_data_path(subpath: str) -> Path:
    """
    Get an absolute path within the data directory.

    Args:
        subpath: Relative path within the data directory.

    Returns:
        Absolute Path object.
    """
    return get_config().data_root / subpath


def get_output_path(subpath: str) -> Path:
    """
    Get an absolute path within the processed output directory.

    Args:
        subpath: Relative path within the processed directory.

    Returns:
        Absolute Path object.
    """
    return get_config().output_root / subpath


def get_code_path(subpath: str) -> Path:
    """
    Get an absolute path within the code directory.

    Args:
        subpath: Relative path within the code directory.

    Returns:
        Absolute Path object.
    """
    return get_config().code_root / subpath


# Initialize seed on module import for immediate reproducibility
set_seed()

logger.info("Configuration module initialized.")
