"""
Configuration management module.

Handles seeds, tolerances, paths, and other global project settings.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


# Default configuration values
DEFAULT_SEED = 42
DEFAULT_OUTLIER_TOLERANCE = 1e-6  # e for epsilon
DEFAULT_N = 1000
DEFAULT_THETA = 2.5


class ProjectConfig:
    """Project-wide configuration container."""

    def __init__(
        self,
        project_root: Optional[Path] = None,
        seed: Optional[int] = None,
        outlier_tolerance: Optional[float] = None,
        default_n: Optional[int] = None,
        default_theta: Optional[float] = None
    ):
        """
        Initialize project configuration.

        Args:
            project_root: Root directory of the project. If None, tries to detect.
            seed: Random seed. Defaults to DEFAULT_SEED.
            outlier_tolerance: Tolerance for outlier detection. Defaults to DEFAULT_OUTLIER_TOLERANCE.
            default_n: Default matrix dimension. Defaults to DEFAULT_N.
            default_theta: Default perturbation strength. Defaults to DEFAULT_THETA.
        """
        self.project_root = project_root or self._detect_project_root()
        self.seed = seed if seed is not None else DEFAULT_SEED
        self.outlier_tolerance = (
            outlier_tolerance if outlier_tolerance is not None else DEFAULT_OUTLIER_TOLERANCE
        )
        self.default_n = default_n if default_n is not None else DEFAULT_N
        self.default_theta = default_theta if default_theta is not None else DEFAULT_THETA

        # Derived paths
        self.code_dir = self.project_root / "code"
        self.data_raw = self.project_root / "data" / "raw"
        self.data_processed = self.project_root / "data" / "processed"
        self.data_figures = self.project_root / "data" / "figures"
        self.data_logs = self.project_root / "data" / "logs"
        self.state_dir = self.project_root / "state"
        self.tests_dir = self.project_root / "tests"

    @staticmethod
    def _detect_project_root() -> Path:
        """Detect the project root by looking for a marker file or directory structure."""
        # Start from current working directory
        cwd = Path.cwd()

        # Look for 'code/' directory as an indicator
        if (cwd / "code").exists():
            return cwd

        # Traverse up
        for parent in cwd.parents:
            if (parent / "code").exists():
                return parent

        # Fallback to cwd
        return cwd


# Global configuration instance
_config: Optional[ProjectConfig] = None


def get_config() -> ProjectConfig:
    """Get or create the global project configuration."""
    global _config
    if _config is None:
        _config = ProjectConfig()
    return _config


def get_seed() -> int:
    """Get the current random seed."""
    return get_config().seed


def get_outlier_tolerance() -> float:
    """Get the outlier detection tolerance (epsilon)."""
    return get_config().outlier_tolerance


def get_project_paths() -> Dict[str, Path]:
    """Get all project paths as a dictionary."""
    cfg = get_config()
    return {
        "project_root": cfg.project_root,
        "code": cfg.code_dir,
        "data_raw": cfg.data_raw,
        "data_processed": cfg.data_processed,
        "data_figures": cfg.data_figures,
        "data_logs": cfg.data_logs,
        "state": cfg.state_dir,
        "tests": cfg.tests_dir,
    }


def set_seed(seed: int) -> None:
    """Set the global random seed."""
    get_config().seed = seed


def set_outlier_tolerance(tolerance: float) -> None:
    """Set the outlier detection tolerance."""
    get_config().outlier_tolerance = tolerance


def load_config_from_file(config_path: Path) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.

    Args:
        config_path: Path to the configuration JSON file.

    Returns:
        Dictionary of configuration values.
    """
    with open(config_path, "r") as f:
        return json.load(f)


def save_config_to_file(config: Dict[str, Any], config_path: Path) -> None:
    """
    Save configuration to a JSON file.

    Args:
        config: Configuration dictionary.
        config_path: Path to save the configuration.
    """
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
