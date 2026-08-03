"""
Configuration management for the phase transition prediction pipeline.

This module defines configuration classes and provides access to configuration
settings via environment variables and default values.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

@dataclass
class PathConfig:
    """Configuration for file paths."""
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    code_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent)
    data_raw_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "raw")
    data_processed_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "processed")
    data_logs_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "logs")
    models_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "artifacts" / "models")
    figures_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "artifacts" / "figures")
    reports_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "docs" / "reports")
    
    def __post_init__(self):
        # Ensure paths are Path objects
        self.project_root = Path(self.project_root)
        self.code_dir = Path(self.code_dir)
        self.data_raw_dir = Path(self.data_raw_dir)
        self.data_processed_dir = Path(self.data_processed_dir)
        self.data_logs_dir = Path(self.data_logs_dir)
        self.models_dir = Path(self.models_dir)
        self.figures_dir = Path(self.figures_dir)
        self.reports_dir = Path(self.reports_dir)

@dataclass
class SimulationConfig:
    """Configuration for MD simulations."""
    cooling_rate: float = float(os.getenv("COOLING_RATE", "1e10"))  # K/s
    experimental_cooling_rate: float = float(os.getenv("EXPERIMENTAL_COOLING_RATE", "1e2"))  # K/s
    time_steps: int = int(os.getenv("TIME_STEPS", "100000"))
    time_step_size: float = float(os.getenv("TIME_STEP_SIZE", "1e-15"))  # seconds
    max_simulation_time: float = float(os.getenv("MAX_SIMULATION_TIME", "1e-7"))  # seconds
    truncation_threshold: int = int(os.getenv("TRUNCATION_THRESHOLD", "500"))  # steps to keep
    
    # OpenKIM potentials
    openkim_potential: str = os.getenv("OPENKIM_POTENTIAL", "MEAM.LAMMPS.Mishin2001.CuAl")
    
    # CPU time cap per composition (seconds)
    cpu_time_cap: float = float(os.getenv("CPU_TIME_CAP", "3600"))

@dataclass
class ModelConfig:
    """Configuration for ML models."""
    # Random Forest parameters
    rf_n_estimators: int = int(os.getenv("RF_N_ESTIMATORS", "100"))
    rf_max_depth: Optional[int] = int(os.getenv("RF_MAX_DEPTH", "10")) if os.getenv("RF_MAX_DEPTH") else None
    rf_min_samples_split: int = int(os.getenv("RF_MIN_SAMPLES_SPLIT", "2"))
    rf_min_samples_leaf: int = int(os.getenv("RF_MIN_SAMPLES_LEAF", "1"))
    
    # Cross-validation
    cv_folds: int = int(os.getenv("CV_FOLDS", "5"))
    
    # Random seed for reproducibility
    random_seed: int = int(os.getenv("RANDOM_SEED", "42"))

@dataclass
class DataConfig:
    """Configuration for data processing."""
    # Data quality thresholds
    nan_threshold: float = float(os.getenv("NAN_THRESHOLD", "0.1"))  # fraction of NaN allowed
    outlier_std_threshold: float = float(os.getenv("OUTLIER_STD_THRESHOLD", "3.0"))
    
    # Feature selection
    feature_selection_method: str = os.getenv("FEATURE_SELECTION_METHOD", "correlation")
    max_features: int = int(os.getenv("MAX_FEATURES", "20"))
    
    # Labeling
    crystallization_threshold: int = int(os.getenv("CRYSTALLIZATION_THRESHOLD", "50"))  # K

@dataclass
class Config:
    """Main configuration class."""
    paths: PathConfig = field(default_factory=PathConfig)
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    data: DataConfig = field(default_factory=DataConfig)

# Global configuration instance
_config: Optional[Config] = None

def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config

def get_simulation_config() -> SimulationConfig:
    """Get simulation configuration."""
    return get_config().simulation

def get_model_config() -> ModelConfig:
    """Get model configuration."""
    return get_config().model

def get_data_config() -> DataConfig:
    """Get data configuration."""
    return get_config().data

def get_paths() -> PathConfig:
    """Get path configuration."""
    return get_config().paths

def reset_config():
    """Reset the global configuration (useful for testing)."""
    global _config
    _config = None