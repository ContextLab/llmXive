"""
Configuration management for the phase transition prediction pipeline.

This module defines configuration dataclasses, provides accessors for
configuration sections, and exposes convenient shortcut properties used
throughout the code base (e.g., ``Config().data_raw``).

It also defines the ``Family`` enum representing chemical families used
in the project.
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv
from enum import Enum

# Load environment variables from a .env file if present
load_dotenv()


@dataclass
class PathConfig:
    """Configuration for file system paths."""

    project_root: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent
    )
    code_dir: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent
    )
    data_raw_dir: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent
        / "data"
        / "raw"
    )
    data_processed_dir: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent
        / "data"
        / "processed"
    )
    data_logs_dir: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent
        / "data"
        / "logs"
    )
    models_dir: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent
        / "artifacts"
        / "models"
    )
    figures_dir: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent
        / "artifacts"
        / "figures"
    )
    reports_dir: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent
        / "docs"
        / "reports"
    )

    def __post_init__(self) -> None:
        # Ensure all attributes are Path objects
        for attr in (
            "project_root",
            "code_dir",
            "data_raw_dir",
            "data_processed_dir",
            "data_logs_dir",
            "models_dir",
            "figures_dir",
            "reports_dir",
        ):
            setattr(self, attr, Path(getattr(self, attr)))


@dataclass
class SimulationConfig:
    """Configuration for MD simulations."""

    cooling_rate: float = float(os.getenv("COOLING_RATE", "1e10"))  # K/s
    experimental_cooling_rate: float = float(
        os.getenv("EXPERIMENTAL_COOLING_RATE", "1e2")
    )  # K/s
    time_steps: int = int(os.getenv("TIME_STEPS", "100000"))
    time_step_size: float = float(os.getenv("TIME_STEP_SIZE", "1e-15"))  # seconds
    max_simulation_time: float = float(
        os.getenv("MAX_SIMULATION_TIME", "1e-7")
    )  # seconds
    truncation_threshold: int = int(
        os.getenv("TRUNCATION_THRESHOLD", "500")
    )  # steps to keep

    # OpenKIM potentials
    openkim_potential: str = os.getenv(
        "OPENKIM_POTENTIAL", "MEAM.LAMMPS.Mishin2001.CuAl"
    )

    # CPU time cap per composition (seconds)
    cpu_time_cap: float = float(os.getenv("CPU_TIME_CAP", "3600"))


@dataclass
class ModelConfig:
    """Configuration for machine‑learning models."""

    # Random Forest parameters
    rf_n_estimators: int = int(os.getenv("RF_N_ESTIMATORS", "100"))
    rf_max_depth: Optional[int] = (
        int(os.getenv("RF_MAX_DEPTH")) if os.getenv("RF_MAX_DEPTH") else None
    )
    rf_min_samples_split: int = int(
        os.getenv("RF_MIN_SAMPLES_SPLIT", "2")
    )
    rf_min_samples_leaf: int = int(
        os.getenv("RF_MIN_SAMPLES_LEAF", "1")
    )

    # Cross‑validation
    cv_folds: int = int(os.getenv("CV_FOLDS", "5"))

    # Random seed for reproducibility
    random_seed: int = int(os.getenv("RANDOM_SEED", "42"))


@dataclass
class DataConfig:
    """Configuration for data processing."""

    # Data quality thresholds
    nan_threshold: float = float(os.getenv("NAN_THRESHOLD", "0.1"))  # fraction of NaN allowed
    outlier_std_threshold: float = float(
        os.getenv("OUTLIER_STD_THRESHOLD", "3.0")
    )

    # Feature selection
    feature_selection_method: str = os.getenv(
        "FEATURE_SELECTION_METHOD", "correlation"
    )
    max_features: int = int(os.getenv("MAX_FEATURES", "20"))

    # Labeling
    crystallization_threshold: int = int(
        os.getenv("CRYSTALLIZATION_THRESHOLD", "50")
    )  # K


class Family(Enum):
    """Enum representing chemical families used in the project."""

    OXIDE = "oxide"
    SULFIDE = "sulfide"
    ORGANIC = "organic"

    def __str__(self) -> str:
        return self.value


@dataclass
class Config:
    """Main configuration container exposing all sub‑configs."""

    paths: PathConfig = field(default_factory=PathConfig)
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    data: DataConfig = field(default_factory=DataConfig)

    # ------------------------------------------------------------------
    # Convenience shortcut properties
    # ------------------------------------------------------------------
    @property
    def data_raw(self) -> Path:
        """Shortcut to the raw data directory (``data/raw/``)."""
        return self.paths.data_raw_dir

    @property
    def data_processed(self) -> Path:
        """Shortcut to the processed data directory (``data/processed/``)."""
        return self.paths.data_processed_dir

    @property
    def random_seed(self) -> int:
        """Global random seed used throughout the pipeline."""
        return self.model.random_seed

    @property
    def cooling_rate(self) -> float:
        """Cooling rate used for MD simulations."""
        return self.simulation.cooling_rate

    @property
    def experimental_cooling_rate(self) -> float:
        """Experimental cooling rate (for timescale matching)."""
        return self.simulation.experimental_cooling_rate


# ----------------------------------------------------------------------
# Global singleton accessor utilities
# ----------------------------------------------------------------------
_config: Optional[Config] = None


def get_config() -> Config:
    """Return the global ``Config`` singleton, creating it on first use."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def get_simulation_config() -> SimulationConfig:
    """Convenient accessor for the ``SimulationConfig`` section."""
    return get_config().simulation


def get_model_config() -> ModelConfig:
    """Convenient accessor for the ``ModelConfig`` section."""
    return get_config().model


def get_data_config() -> DataConfig:
    """Convenient accessor for the ``DataConfig`` section."""
    return get_config().data


def get_paths() -> PathConfig:
    """Convenient accessor for the ``PathConfig`` section."""
    return get_config().paths


def reset_config() -> None:
    """Reset the global configuration singleton (useful for tests)."""
    global _config
    _config = None
    # Explicitly delete any cached environment variables that may have changed
    # during a test run. This ensures a fresh ``Config`` instance picks up
    # the current environment.
    os.environ.pop("COOLING_RATE", None)
    os.environ.pop("EXPERIMENTAL_COOLING_RATE", None)
    os.environ.pop("CPU_TIME_CAP", None)
    os.environ.pop("RANDOM_SEED", None)