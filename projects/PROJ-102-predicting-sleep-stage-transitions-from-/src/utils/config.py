"""
Configuration management for the Sleep Stage Transition Prediction pipeline.

This module provides centralized configuration for paths, random seeds,
data processing parameters, and model hyperparameters.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict

# Global configuration instance
_global_config: Optional['Config'] = None


@dataclass
class PathConfig:
    """Project directory paths."""
    root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent)
    data_raw: Path = field(init=False)
    data_processed: Path = field(init=False)
    data_interim: Path = field(init=False)
    src: Path = field(init=False)
    tests: Path = field(init=False)
    specs: Path = field(init=False)
    figures: Path = field(init=False)

    def __post_init__(self):
        """Initialize derived paths relative to root."""
        self.data_raw = self.root / "data" / "raw"
        self.data_processed = self.root / "data" / "processed"
        self.data_interim = self.root / "data" / "interim"
        self.src = self.root / "src"
        self.tests = self.root / "tests"
        self.specs = self.root / "specs"
        self.figures = self.root / "figures"

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary with string paths."""
        return {k: str(v) for k, v in asdict(self).items()}


@dataclass
class SeedConfig:
    """Random seed configuration for reproducibility."""
    numpy: int = 42
    python: int = 42
    torch: Optional[int] = None  # Only if torch is used
    tensorflow: Optional[int] = None  # Only if tensorflow is used


@dataclass
class DataConfig:
    """Data processing and loading configuration."""
    # Sleep-EDF specific
    subject_ids: list = field(default_factory=lambda: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    use_all_subjects: bool = False
    
    # Signal processing
    sampling_rate: float = 100.0  # Hz (target resampling rate)
    original_sampling_rate: float = 100.0  # Hz (Sleep-EDF SC native rate)
    bandpass_low: float = 0.5  # Hz
    bandpass_high: float = 45.0  # Hz
    notch_frequencies: list = field(default_factory=lambda: [50.0, 60.0])  # Hz
    
    # Windowing
    epoch_duration: int = 30  # seconds
    transition_window_duration: int = 60  # seconds (centered)
    pre_transition_window_duration: int = 60  # seconds (ending 30s before transition)
    
    # Data loading
    batch_size: int = 32
    num_workers: int = 0  # 0 for single-threaded loading
    shuffle: bool = True
    validation_split: float = 0.1
    test_split: float = 0.1
    
    # Feature extraction
    feature_types: list = field(default_factory=lambda: ['time', 'frequency', 'nonlinear'])
    sample_entropy_beta: float = 0.2
    sample_entropy_tolerance: float = 0.2
    
    # Fallback strategies
    use_eog_if_available: bool = True
    fallback_to_re_scoring: bool = True


@dataclass
class ModelConfig:
    """Model architecture and training configuration."""
    # Architecture constraints
    max_parameters: int = 100000  # 100k parameters limit
    input_channels: int = 1  # EEG channel count (can be adjusted)
    input_length: int = 6000  # 60 seconds @ 100 Hz
    
    # CNN architecture
    num_filters: int = 32
    kernel_size: int = 15
    dropout_rate: float = 0.5
    l2_regularization: float = 1e-4
    
    # Training
    optimizer: str = "adam"
    learning_rate: float = 1e-3
    weight_decay: float = 1e-4
    epochs: int = 50
    early_stopping_patience: int = 10
    batch_size: int = 32
    
    # Loss function
    loss_function: str = "binary_cross_entropy"
    class_weight: Optional[Dict[int, float]] = None
    
    # Evaluation
    metrics: list = field(default_factory=lambda: ['accuracy', 'precision', 'recall', 'f1'])
    validation_metric: str = 'f1'
    
    # Cross-validation
    cv_folds: int = 5
    leave_one_subject_out: bool = True
    
    # Output
    checkpoint_path: str = "model_checkpoint.pth"
    metrics_path: str = "metrics.json"


@dataclass
class Config:
    """Master configuration container."""
    paths: PathConfig = field(default_factory=PathConfig)
    seeds: SeedConfig = field(default_factory=SeedConfig)
    data: DataConfig = field(default_factory=DataConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entire config to dictionary."""
        return {
            'paths': self.paths.to_dict(),
            'seeds': asdict(self.seeds),
            'data': asdict(self.data),
            'model': asdict(self.model)
        }
    
    def save(self, filepath: Optional[Path] = None) -> None:
        """Save configuration to JSON file."""
        if filepath is None:
            filepath = self.paths.root / "config.json"
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, filepath: Path) -> 'Config':
        """Load configuration from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        config = cls()
        config.paths = PathConfig(**{k: Path(v) for k, v in data['paths'].items()})
        config.seeds = SeedConfig(**data['seeds'])
        config.data = DataConfig(**data['data'])
        config.model = ModelConfig(**data['model'])
        return config


def get_config() -> Config:
    """Get the global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config


def reset_config() -> None:
    """Reset the global configuration to defaults."""
    global _global_config
    _global_config = Config()


def save_config(filepath: Optional[Path] = None) -> None:
    """Save the global configuration to a file."""
    config = get_config()
    config.save(filepath)


# Convenience functions
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
