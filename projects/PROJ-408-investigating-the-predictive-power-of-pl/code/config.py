"""
Configuration management for the llmXive phylogeny-metabolite prediction pipeline.

This module manages paths, API keys, random seeds, and data retention thresholds.
It ensures all configuration is loaded from environment variables or defaults,
with strict validation to prevent silent failures.
"""

import os
import random
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class Config:
    """
    Central configuration holder for the project.

    Attributes:
        project_root: Root directory of the project.
        data_raw_dir: Directory for raw downloaded data.
        data_processed_dir: Directory for processed data.
        output_figures_dir: Directory for generated figures.
        output_reports_dir: Directory for generated reports.
        state_dir: Directory for project state files (e.g., checksums).
        api_keys: Dictionary of API keys (NCBI, etc.).
        random_seed: Global random seed for reproducibility.
        retention_threshold: Minimum proportion of data required to proceed (e.g., 0.8).
        max_workers: Maximum number of parallel workers for I/O tasks.
        mafft_path: Path to the mafft binary.
        fasttree_path: Path to the fasttree binary.
    """
    project_root: Path
    data_raw_dir: Path
    data_processed_dir: Path
    output_figures_dir: Path
    output_reports_dir: Path
    state_dir: Path
    api_keys: Dict[str, str] = field(default_factory=dict)
    random_seed: int = 42
    retention_threshold: float = 0.80
    max_workers: int = 4
    mafft_path: str = "mafft"
    fasttree_path: str = "fasttree"
    email_address: str = "anonymous@example.com"  # Required for NCBI Entrez
    ncbi_api_key: Optional[str] = None

    def __post_init__(self):
        """Validate paths and ensure directories exist."""
        # Ensure project root exists
        if not self.project_root.exists():
            raise ValueError(f"Project root directory does not exist: {self.project_root}")

        # Create required directories if they don't exist
        self._ensure_dir(self.data_raw_dir)
        self._ensure_dir(self.data_processed_dir)
        self._ensure_dir(self.output_figures_dir)
        self._ensure_dir(self.output_reports_dir)
        self._ensure_dir(self.state_dir)

    @staticmethod
    def _ensure_dir(path: Path):
        """Ensure a directory exists, creating it if necessary."""
        path.mkdir(parents=True, exist_ok=True)

    def get_path(self, relative_path: str) -> Path:
        """
        Get an absolute path relative to the project root.

        Args:
            relative_path: Relative path string.

        Returns:
            Absolute Path object.
        """
        return self.project_root / relative_path

    def get_data_path(self, relative_path: str) -> Path:
        """Get path relative to data_raw_dir."""
        return self.data_raw_dir / relative_path

    def get_processed_path(self, relative_path: str) -> Path:
        """Get path relative to data_processed_dir."""
        return self.data_processed_dir / relative_path

    def get_figure_path(self, relative_path: str) -> Path:
        """Get path relative to output_figures_dir."""
        return self.output_figures_dir / relative_path

    def get_report_path(self, relative_path: str) -> Path:
        """Get path relative to output_reports_dir."""
        return self.output_reports_dir / relative_path

    def set_random_seed(self):
        """Set the global random seed for reproducibility."""
        random.seed(self.random_seed)
        # Also seed numpy if available
        try:
            import numpy as np
            np.random.seed(self.random_seed)
        except ImportError:
            pass

    def validate_api_keys(self):
        """
        Validate that required API keys are present.
        Raises ValueError if critical keys are missing.
        """
        missing_keys = []
        if not self.api_keys.get("ncbi_email"):
            missing_keys.append("NCBI_EMAIL")
        
        if self.ncbi_api_key is None and os.environ.get("NCBI_API_KEY_REQUIRED", "false").lower() == "true":
            missing_keys.append("NCBI_API_KEY")

        if missing_keys:
            raise ValueError(f"Missing required API keys or configuration: {', '.join(missing_keys)}")


def load_config() -> Config:
    """
    Load configuration from environment variables and defaults.

    Returns:
        Config object with validated settings.
    """
    # Determine project root (assumed to be parent of 'code' directory)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    # Load environment variables
    data_raw = os.environ.get("DATA_RAW_DIR", "data/raw")
    data_processed = os.environ.get("DATA_PROCESSED_DIR", "data/processed")
    output_figures = os.environ.get("OUTPUT_FIGURES_DIR", "output/figures")
    output_reports = os.environ.get("OUTPUT_REPORTS_DIR", "output/reports")
    state_dir = os.environ.get("STATE_DIR", "state/projects")

    # Convert to absolute paths
    data_raw_path = project_root / data_raw
    data_processed_path = project_root / data_processed
    output_figures_path = project_root / output_figures
    output_reports_path = project_root / output_reports
    state_dir_path = project_root / state_dir

    # API Keys
    api_keys = {}
    ncbi_email = os.environ.get("NCBI_EMAIL", "")
    if ncbi_email:
        api_keys["ncbi_email"] = ncbi_email

    ncbi_api_key = os.environ.get("NCBI_API_KEY")
    if ncbi_api_key:
        api_keys["ncbi_api_key"] = ncbi_api_key

    # Random seed
    random_seed = int(os.environ.get("RANDOM_SEED", "42"))

    # Retention threshold (default 80%)
    retention_threshold = float(os.environ.get("RETENTION_THRESHOLD", "0.80"))

    # Max workers
    max_workers = int(os.environ.get("MAX_WORKERS", "4"))

    # Binary paths (can be overridden by env, defaults to PATH)
    mafft_path = os.environ.get("MAFFT_PATH", "mafft")
    fasttree_path = os.environ.get("FASTTREE_PATH", "fasttree")

    config = Config(
        project_root=project_root,
        data_raw_dir=data_raw_path,
        data_processed_dir=data_processed_path,
        output_figures_dir=output_figures_path,
        output_reports_dir=output_reports_path,
        state_dir=state_dir_path,
        api_keys=api_keys,
        random_seed=random_seed,
        retention_threshold=retention_threshold,
        max_workers=max_workers,
        mafft_path=mafft_path,
        fasttree_path=fasttree_path,
        email_address=ncbi_email,
        ncbi_api_key=ncbi_api_key
    )

    return config


# Global config instance (lazy initialization)
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        Config object.
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reset_config():
    """Reset the global configuration instance (useful for testing)."""
    global _config
    _config = None


# Utility functions for checksums
def calculate_checksum(file_path: Path) -> str:
    """
    Calculate SHA256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hex digest of the SHA256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def validate_file_integrity(file_path: Path, expected_checksum: str) -> bool:
    """
    Validate file integrity against expected checksum.

    Args:
        file_path: Path to the file.
        expected_checksum: Expected SHA256 hash.

    Returns:
        True if checksum matches, False otherwise.
    """
    actual_checksum = calculate_checksum(file_path)
    return actual_checksum == expected_checksum
