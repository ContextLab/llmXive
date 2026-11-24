"""
src/config.py

Central configuration module for the statistical analysis pipeline.

This module provides:
- A dataclass ``Config`` that holds all hyperparameters, directory paths,
  random seeds, and compute limits.
- Helper functions ``get_config`` and ``set_config`` to access a global
  singleton instance (useful throughout the code base and in tests).
- Automatic creation of required directories.
- Environment variable overrides for key settings.
- Ability to save and load the configuration to/from a YAML snapshot.
"""

import os
import random
import yaml
import numpy as np
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

@dataclass
class Config:
    """
    Configuration container.

    All fields have sensible defaults; they can be overridden by
    environment variables or by loading a saved YAML snapshot.
    """

    # ------------------------------------------------------------------
    # Paths (derived from ``project_root`` in ``__post_init__``)
    # ------------------------------------------------------------------
    project_root: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent
    )
    data_raw_dir: Path = field(init=False)
    data_processed_dir: Path = field(init=False)
    outputs_plots_dir: Path = field(init=False)
    outputs_metrics_dir: Path = field(init=False)
    state_dir: Path = field(init=False)
    specs_dir: Path = field(init=False)

    # ------------------------------------------------------------------
    # Hyper‑parameters for the analysis
    # ------------------------------------------------------------------
    training_start_year: int = 2000
    training_end_year: int = 2015
    test_start_year: int = 2019
    test_end_year: int = 2020

    # Extreme‑event definition
    percentile_threshold: float = 95.0  # percentile used for peaks‑over‑threshold
    missing_ratio_threshold: float = 0.15  # max allowed overall missing ratio
    max_contiguous_gap_days: int = 30    # max allowed consecutive missing days

    # Model‑specific defaults (can be overridden later)
    gpd_loc_param: float = 0.0
    gpd_scale_param: float = 1.0
    gpd_shape_param: float = 0.0

    # ------------------------------------------------------------------
    # Compute limits
    # ------------------------------------------------------------------
    wall_clock_budget_seconds: int = 6 * 60 * 60  # 6 hours
    time_limit_check_interval_seconds: int = 300  # 5 minutes

    # ------------------------------------------------------------------
    # Randomness & logging
    # ------------------------------------------------------------------
    seed: int = 42
    log_level: str = "INFO"
    log_file: Optional[str] = None

    def __post_init__(self) -> None:
        """Create derived paths and apply environment overrides."""
        # Derived directories (always relative to the repository root)
        self.data_raw_dir = self.project_root / "data" / "raw"
        self.data_processed_dir = self.project_root / "data" / "processed"
        self.outputs_plots_dir = self.project_root / "outputs" / "plots"
        self.outputs_metrics_dir = self.project_root / "outputs" / "metrics"
        self.state_dir = self.project_root / "state"
        self.specs_dir = self.project_root / "specs"

        # Ensure the directories exist
        for p in (
            self.data_raw_dir,
            self.data_processed_dir,
            self.outputs_plots_dir,
            self.outputs_metrics_dir,
            self.state_dir,
            self.specs_dir,
        ):
            p.mkdir(parents=True, exist_ok=True)

        # Apply any overrides from the environment
        self._apply_env_overrides()

        # Initialise random seeds for reproducibility
        random.seed(self.seed)
        np.random.seed(self.seed)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _apply_env_overrides(self) -> None:
        """Override configuration values with ``PIPELINE_*`` environment variables."""
        if env_seed := os.getenv("PIPELINE_SEED"):
            self.seed = int(env_seed)

        if env_budget := os.getenv("PIPELINE_WALL_CLOCK_BUDGET_SECONDS"):
            self.wall_clock_budget_seconds = int(env_budget)

        if env_threshold := os.getenv("PIPELINE_PERCENTILE_THRESHOLD"):
            self.percentile_threshold = float(env_threshold)

        # Additional optional overrides
        if env_missing := os.getenv("PIPELINE_MISSING_RATIO_THRESHOLD"):
            self.missing_ratio_threshold = float(env_missing)

        if env_gap := os.getenv("PIPELINE_MAX_CONTIGUOUS_GAP_DAYS"):
            self.max_contiguous_gap_days = int(env_gap)

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        """Return a plain‑dict representation (useful for YAML dumping)."""
        return {
            "project_root": str(self.project_root),
            "paths": {
                "data_raw": str(self.data_raw_dir),
                "data_processed": str(self.data_processed_dir),
                "outputs_plots": str(self.outputs_plots_dir),
                "outputs_metrics": str(self.outputs_metrics_dir),
                "state": str(self.state_dir),
                "specs": str(self.specs_dir),
            },
            "training_years": f"{self.training_start_year}-{self.training_end_year}",
            "test_years": f"{self.test_start_year}-{self.test_end_year}",
            "percentile_threshold": self.percentile_threshold,
            "missing_ratio_threshold": self.missing_ratio_threshold,
            "max_contiguous_gap_days": self.max_contiguous_gap_days,
            "wall_clock_budget_seconds": self.wall_clock_budget_seconds,
            "time_limit_check_interval_seconds": self.time_limit_check_interval_seconds,
            "seed": self.seed,
            "log_level": self.log_level,
            "log_file": self.log_file,
        }

    def save_yaml(self, path: Optional[Path] = None) -> None:
        """
        Persist the current configuration to a YAML file.

        By default the snapshot is written to ``state/config_snapshot.yaml``.
        """
        if path is None:
            path = self.state_dir / "config_snapshot.yaml"
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)

    @classmethod
    def load_yaml(cls, path: Path) -> "Config":
        """
        Load a configuration from a YAML file and return a ``Config`` instance.

        Only the keys present in the snapshot are applied; missing keys keep
        their default values.
        """
        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}

        cfg = cls()

        # Populate simple scalar overrides
        if training := data.get("training_years"):
            start, end = map(int, training.split("-"))
            cfg.training_start_year = start
            cfg.training_end_year = end

        if test := data.get("test_years"):
            start, end = map(int, test.split("-"))
            cfg.test_start_year = start
            cfg.test_end_year = end

        if pct := data.get("percentile_threshold"):
            cfg.percentile_threshold = float(pct)

        if missing := data.get("missing_ratio_threshold"):
            cfg.missing_ratio_threshold = float(missing)

        if gap := data.get("max_contiguous_gap_days"):
            cfg.max_contiguous_gap_days = int(gap)

        if budget := data.get("wall_clock_budget_seconds"):
            cfg.wall_clock_budget_seconds = int(budget)

        if seed := data.get("seed"):
            cfg.seed = int(seed)

        # Apply environment overrides after loading from file
        cfg._apply_env_overrides()
        return cfg

# ----------------------------------------------------------------------
# Global singleton handling
# ----------------------------------------------------------------------
_config_instance: Optional[Config] = None

def get_config() -> Config:
    """
    Retrieve the global ``Config`` instance.

    If it does not exist yet, the function attempts to load a previously
    saved snapshot from ``state/config_snapshot.yaml``; otherwise a fresh
    ``Config`` with defaults is created.
    """
    global _config_instance
    if _config_instance is None:
        snapshot_path = (
            Path(__file__).resolve().parent.parent.parent
            / "state"
            / "config_snapshot.yaml"
        )
        if snapshot_path.exists():
            _config_instance = Config.load_yaml(snapshot_path)
        else:
            _config_instance = Config()
    return _config_instance

def set_config(config: Config) -> None:
    """
    Replace the global configuration singleton (mainly useful in tests).
    """
    global _config_instance
    _config_instance = config

# ----------------------------------------------------------------------
# Simple sanity‑check when the module is executed directly
# ----------------------------------------------------------------------
if __name__ == "__main__":
    cfg = get_config()
    print("Configuration loaded:")
    for k, v in cfg.to_dict().items():
        print(f"  {k}: {v}")
    # Persist a snapshot for downstream steps
    cfg.save_yaml()
    print(f"\nSnapshot saved to: {cfg.state_dir / 'config_snapshot.yaml'}")