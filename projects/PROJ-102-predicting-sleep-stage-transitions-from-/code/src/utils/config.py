"""
Configuration management for the Sleep Stage Transition Prediction pipeline.

This module provides centralized management for:
- File system paths (raw, processed, interim data)
- Random seeds for reproducibility
- Model hyperparameters
- Data processing parameters
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class PathConfig:
    """Configuration for all project paths."""
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent.parent)
    data_dir: Path = field(init=False)
    data_raw: Path = field(init=False)
    data_processed: Path = field(init=False)
    data_interim: Path = field(init=False)
    src_dir: Path = field(init=False)
    features_dir: Path = field(init=False)
    models_dir: Path = field(init=False)
    utils_dir: Path = field(init=False)
    tests_dir: Path = field(init=False)
    specs_dir: Path = field(init=False)
    figures_dir: Path = field(init=False)

    def __post_init__(self):
        self.data_dir = self.project_root / "data"
        self.data_raw = self.data_dir / "raw"
        self.data_processed = self.data_dir / "processed"
        self.data_interim = self.data_dir / "interim"
        self.src_dir = self.project_root / "src"
        self.features_dir = self.src_dir / "features"
        self.models_dir = self.src_dir / "models"
        self.utils_dir = self.src_dir / "utils"
        self.tests_dir = self.project_root / "tests"
        self.specs_dir = self.project_root / "specs"
        self.figures_dir = self.project_root / "figures"

    def ensure_directories(self) -> None:
        """Create all required directories if they don't exist."""
        for path in [
            self.data_raw,
            self.data_processed,
            self.data_interim,
            self.features_dir,
            self.models_dir,
            self.utils_dir,
            self.tests_dir,
            self.specs_dir,
            self.figures_dir
        ]:
            path.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> Dict[str, str]:
        """Convert paths to dictionary with string values."""
        return {k: str(v) for k, v in asdict(self).items()}


@dataclass
class SeedConfig:
    """Configuration for random seeds to ensure reproducibility."""
    numpy_seed: int = 42
    python_seed: int = 42
    torch_seed: Optional[int] = 42  # Optional for torch if available
    tensorflow_seed: Optional[int] = 42  # Optional for tensorflow if available

    def set_all(self) -> None:
        """Set all random seeds for reproducibility."""
        import random
        random.seed(self.python_seed)

        import numpy as np
        np.random.seed(self.numpy_seed)

        try:
            import torch
            torch.manual_seed(self.torch_seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(self.torch_seed)
        except ImportError:
            pass

        try:
            import tensorflow as tf
            tf.random.set_seed(self.tensorflow_seed)
        except ImportError:
            pass


@dataclass
class DataConfig:
    """Configuration for data processing parameters."""
    # Sleep-EDF specific
    sleep_edf_url: str = "https://physionet.org/files/sleep-edfx/1.0.0/"
    sleep_edf_subset: list = field(default_factory=lambda: [
        "SC-Study1-001", "SC-Study1-002", "SC-Study1-003",
        "SC-Study1-004", "SC-Study1-005", "SC-Study1-006",
        "SC-Study1-007", "SC-Study1-008", "SC-Study1-009",
        "SC-Study1-010"
    ])
    checksums: Dict[str, str] = field(default_factory=lambda: {})

    # Preprocessing
    sampling_rate: float = 100.0  # Hz (downsampled from original)
    notch_frequencies: list = field(default_factory=lambda: [50, 60])  # Hz
    bandpass_low: float = 0.5  # Hz
    bandpass_high: float = 45.0  # Hz
    interpolation_method: str = "linear"

    # Segmentation
    epoch_duration: int = 30  # seconds (standard sleep staging)
    transition_window_duration: int = 60  # seconds (centered on transition)
    pre_transition_duration: int = 60  # seconds (input window ending 30s before transition)

    # Feature extraction
    feature_types: list = field(default_factory=lambda: [
        "time_domain",
        "frequency_domain",
        "non_linear"
    ])
    delta_band: tuple = field(default_factory=lambda: (0.5, 4.0))
    theta_band: tuple = field(default_factory=lambda: (4.0, 8.0))
    alpha_band: tuple = field(default_factory=lambda: (8.0, 13.0))
    sigma_band: tuple = field(default_factory=lambda: (13.0, 16.0))
    beta_band: tuple = field(default_factory=lambda: (16.0, 30.0))
    gamma_band: tuple = field(default_factory=lambda: (30.0, 45.0))


@dataclass
class ModelConfig:
    """Configuration for model architecture and training."""
    # Architecture constraints
    max_params: int = 100_000  # Maximum model parameters
    input_channels: int = 1  # EEG channel count
    sequence_length: int = 3000  # 30s @ 100Hz

    # Training hyperparameters
    learning_rate: float = 1e-3
    batch_size: int = 32
    num_epochs: int = 50
    weight_decay: float = 1e-4  # L2 regularization
    dropout_rate: float = 0.3

    # Optimization
    optimizer: str = "adam"
    scheduler: str = "reduce_on_plateau"
    patience: int = 10  # Early stopping patience

    # Validation
    loso_folds: bool = True  # Leave-one-subject-out cross-validation
    random_split: bool = False
    test_split_ratio: float = 0.2

    # Metrics
    metric: str = "accuracy"
    target_improvement: float = 0.05  # 5% improvement over random baseline


@dataclass
class Config:
    """Main configuration class aggregating all settings."""
    paths: PathConfig = field(default_factory=PathConfig)
    seeds: SeedConfig = field(default_factory=SeedConfig)
    data: DataConfig = field(default_factory=DataConfig)
    model: ModelConfig = field(default_factory=ModelConfig)

    def save(self, filepath: Optional[Path] = None) -> Path:
        """Save configuration to JSON file."""
        if filepath is None:
            filepath = self.paths.data_processed / "config.json"

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        config_dict = {
            "paths": self.paths.to_dict(),
            "seeds": asdict(self.seeds),
            "data": asdict(self.data),
            "model": asdict(self.model)
        }

        with open(filepath, 'w') as f:
            json.dump(config_dict, f, indent=2)

        return filepath

    @classmethod
    def load(cls, filepath: Path) -> 'Config':
        """Load configuration from JSON file."""
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Configuration file not found: {filepath}")

        with open(filepath, 'r') as f:
            config_dict = json.load(f)

        config = cls()
        config.paths = PathConfig(**{k: Path(v) for k, v in config_dict["paths"].items()})
        config.seeds = SeedConfig(**config_dict["seeds"])
        config.data = DataConfig(**config_dict["data"])
        config.model = ModelConfig(**config_dict["model"])

        return config

    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        self.paths.ensure_directories()


# Singleton instance for global access
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create the global configuration singleton."""
    global _config
    if _config is None:
        _config = Config()
        _config.ensure_directories()
    return _config


def reset_config() -> None:
    """Reset the global configuration singleton (useful for testing)."""
    global _config
    _config = None


def save_config(filepath: Optional[Path] = None) -> Path:
    """Save the current configuration to a file."""
    config = get_config()
    return config.save(filepath)


# Convenience accessors
def get_paths() -> PathConfig:
    """Get path configuration."""
    return get_config().paths


def get_seeds() -> SeedConfig:
    """Get seed configuration."""
    return get_config().seeds


def get_data_config() -> DataConfig:
    """Get data configuration."""
    return get_config().data


def get_model_config() -> ModelConfig:
    """Get model configuration."""
    return get_config().model
