"""
Environment configuration management for random seeds and file paths.

This module provides a centralized configuration class to manage:
- Random seeds for reproducibility (numpy, python, torch if available)
- File paths for data, models, logs, and figures
- Project-specific settings loaded from environment variables or defaults
"""

import os
import random
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Import logger from existing utility
from code.utils.logger import setup_logger

logger = setup_logger(__name__)

class Config:
    """
    Centralized configuration manager for the project.

    Attributes:
        project_root (Path): Root directory of the project.
        data_raw (Path): Path to raw data directory.
        data_processed (Path): Path to processed data directory.
        data_models (Path): Path to store model artifacts.
        figures (Path): Path to store generated figures.
        logs (Path): Path to log files.
        random_seed (int): Global random seed for reproducibility.
        eas_min_count (int): Minimum required EAS reactions (gate logic).
        vif_threshold (float): Variance Inflation Factor threshold for collinearity.
        p_value_threshold (float): Bonferroni-corrected significance threshold.
        r_squared_threshold (float): Minimum R² threshold for model validity.
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        random_seed: Optional[int] = None,
        eas_min_count: Optional[int] = None,
        vif_threshold: Optional[float] = None,
        p_value_threshold: Optional[float] = None,
        r_squared_threshold: Optional[float] = None,
    ):
        """
        Initialize the configuration.

        Args:
            project_root: Optional override for project root. Defaults to parent of this file.
            random_seed: Optional override for random seed. Defaults to env var or 42.
            eas_min_count: Minimum EAS count for pipeline gate.
            vif_threshold: VIF cutoff for collinearity.
            p_value_threshold: P-value cutoff for significance.
            r_squared_threshold: R² cutoff for model acceptance.
        """
        # Determine project root
        if project_root:
            self.project_root = Path(project_root)
        else:
            # Default to parent of code/config.py
            self.project_root = Path(__file__).resolve().parent.parent

        # Validate project root exists (fail loudly if not)
        if not self.project_root.exists():
            raise FileNotFoundError(
                f"Project root does not exist: {self.project_root}. "
                "Ensure T001/T004 have been completed to create the directory structure."
            )

        # Initialize paths
        self.data_raw = self.project_root / "data" / "raw"
        self.data_processed = self.project_root / "data" / "processed"
        self.data_models = self.project_root / "data" / "models"
        self.figures = self.project_root / "figures"
        self.logs = self.project_root / "logs"
        self.code_dir = self.project_root / "code"
        self.tests_dir = self.project_root / "tests"
        self.specs_dir = self.project_root / "specs"

        # Ensure directories exist
        self._ensure_directories()

        # Configuration values
        self.random_seed = self._get_int_env(
            "RANDOM_SEED",
            random_seed,
            42
        )
        self.eas_min_count = self._get_int_env(
            "EAS_MIN_COUNT",
            eas_min_count,
            100
        )
        self.vif_threshold = self._get_float_env(
            "VIF_THRESHOLD",
            vif_threshold,
            5.0
        )
        self.p_value_threshold = self._get_float_env(
            "P_VALUE_THRESHOLD",
            p_value_threshold,
            0.0167
        )
        self.r_squared_threshold = self._get_float_env(
            "R_SQUARED_THRESHOLD",
            r_squared_threshold,
            0.05
        )

        # Set random seeds for reproducibility
        self._set_seeds()

        logger.info(f"Configuration initialized. Project root: {self.project_root}")
        logger.info(f"Random seed set to: {self.random_seed}")

    def _ensure_directories(self) -> None:
        """Create all required directories if they do not exist."""
        dirs = [
            self.data_raw,
            self.data_processed,
            self.data_models,
            self.figures,
            self.logs,
            self.code_dir,
            self.tests_dir,
            self.specs_dir,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {d}")

    def _get_int_env(
        self,
        key: str,
        override: Optional[int],
        default: int
    ) -> int:
        """Get an integer from environment, override, or default."""
        if override is not None:
            return override
        env_val = os.getenv(key)
        if env_val:
            try:
                return int(env_val)
            except ValueError:
                logger.warning(f"Invalid integer for {key}: {env_val}. Using default {default}.")
        return default

    def _get_float_env(
        self,
        key: str,
        override: Optional[float],
        default: float
    ) -> float:
        """Get a float from environment, override, or default."""
        if override is not None:
            return override
        env_val = os.getenv(key)
        if env_val:
            try:
                return float(env_val)
            except ValueError:
                logger.warning(f"Invalid float for {key}: {env_val}. Using default {default}.")
        return default

    def _set_seeds(self) -> None:
        """Set random seeds for python, numpy, and torch (if available)."""
        random.seed(self.random_seed)
        try:
            import numpy as np
            np.random.seed(self.random_seed)
        except ImportError:
            logger.warning("NumPy not found. Skipping numpy seed setting.")

        try:
            import torch
            torch.manual_seed(self.random_seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed(self.random_seed)
                torch.cuda.manual_seed_all(self.random_seed)
        except ImportError:
            logger.debug("PyTorch not found. Skipping torch seed setting.")

    def get_config_dict(self) -> Dict[str, Any]:
        """Return a dictionary representation of the configuration."""
        return {
            "project_root": str(self.project_root),
            "data_raw": str(self.data_raw),
            "data_processed": str(self.data_processed),
            "data_models": str(self.data_models),
            "figures": str(self.figures),
            "logs": str(self.logs),
            "random_seed": self.random_seed,
            "eas_min_count": self.eas_min_count,
            "vif_threshold": self.vif_threshold,
            "p_value_threshold": self.p_value_threshold,
            "r_squared_threshold": self.r_squared_threshold,
        }

    def validate_paths(self) -> None:
        """
        Validate that critical paths exist and are writable.
        Raises FileNotFoundError if a critical path is missing.
        """
        critical_paths = [
            ("data_raw", self.data_raw),
            ("data_processed", self.data_processed),
            ("data_models", self.data_models),
            ("logs", self.logs),
        ]
        for name, path in critical_paths:
            if not path.exists():
                raise FileNotFoundError(
                    f"Critical path missing: {name} -> {path}. "
                    "Run T004 to ensure directory structure is created."
                )
            if not os.access(path, os.W_OK):
                raise PermissionError(
                    f"Path not writable: {name} -> {path}."
                )
        logger.info("Path validation successful.")

# Singleton instance for global access
_config_instance: Optional[Config] = None

def get_config() -> Config:
    """
    Get the global configuration singleton.
    Initializes it if it hasn't been initialized yet.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def reset_config() -> None:
    """Reset the global configuration singleton (useful for testing)."""
    global _config_instance
    _config_instance = None

if __name__ == "__main__":
    # Simple test to verify configuration loads and paths exist
    cfg = get_config()
    print(f"Project Root: {cfg.project_root}")
    print(f"Data Processed: {cfg.data_processed}")
    print(f"Random Seed: {cfg.random_seed}")
    print(f"EAS Min Count: {cfg.eas_min_count}")
    cfg.validate_paths()
    print("Configuration validation passed.")