"""
Configuration management for the llmXive heat transport pipeline.

Handles path resolution, mode selection (REAL vs SYNTHETIC), and
environment-based overrides.
"""
import os
from pathlib import Path
from enum import Enum
from typing import Optional

# Project root is the parent of the 'code' directory
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

class RunMode(Enum):
    """Execution mode for the pipeline."""
    REAL = "real"
    SYNTHETIC = "synthetic"

class Config:
    """
    Central configuration object.
    Provides typed access to paths and runtime flags.
    """

    def __init__(self):
        self._project_root: Path = _PROJECT_ROOT
        self._data_root: Path = self._project_root / "data"
        self._raw_data_root: Path = self._data_root / "raw"
        self._processed_data_root: Path = self._data_root / "processed"
        self._contracts_root: Path = self._data_root / "contracts"
        self._figures_root: Path = self._project_root / "figures"
        self._audit_log_path: Path = self._data_root / "audit_log.json"
        
        # Mode selection: Defaults to REAL, can be overridden by env var
        # Env var: PIPELINE_MODE (values: 'real', 'synthetic')
        mode_str = os.getenv("PIPELINE_MODE", "real").lower()
        try:
            self.run_mode = RunMode(mode_str)
        except ValueError:
            raise ValueError(
                f"Invalid PIPELINE_MODE '{mode_str}'. Must be 'real' or 'synthetic'."
            )

        # Completeness threshold for data audit (SC-003)
        self.min_completeness_threshold = 0.90

        # Statistical significance levels
        self.alpha = 0.05

    @property
    def project_root(self) -> Path:
        return self._project_root

    @property
    def data_root(self) -> Path:
        return self._data_root

    @property
    def raw_data_root(self) -> Path:
        return self._raw_data_root

    @property
    def processed_data_root(self) -> Path:
        return self._processed_data_root

    @property
    def contracts_root(self) -> Path:
        return self._contracts_root

    @property
    def figures_root(self) -> Path:
        return self._figures_root

    @property
    def audit_log_path(self) -> Path:
        return self._audit_log_path

    def ensure_directories(self) -> None:
        """
        Creates all required directories if they do not exist.
        Must be called before any data processing begins.
        """
        self._raw_data_root.mkdir(parents=True, exist_ok=True)
        self._processed_data_root.mkdir(parents=True, exist_ok=True)
        self._contracts_root.mkdir(parents=True, exist_ok=True)
        self._figures_root.mkdir(parents=True, exist_ok=True)

    def is_real_mode(self) -> bool:
        return self.run_mode == RunMode.REAL

    def is_synthetic_mode(self) -> bool:
        return self.run_mode == RunMode.SYNTHETIC

# Singleton instance
config = Config()