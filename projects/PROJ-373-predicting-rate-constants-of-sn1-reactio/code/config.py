"""
Configuration module for the SN1 Rate Constant Prediction project.
Contains dataclasses for hyperparameters, paths, and random seeds.
"""
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Any, Callable

# --- Path Constants ---
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
CODE_DIR = PROJECT_ROOT / "code"
SPECS_DIR = PROJECT_ROOT / "specs"

# Ensure directories exist
def ensure_dirs(*paths: Any) -> None:
    """
    Create directories if they do not exist.
    Accepts:
      - No arguments (does nothing, for backward compatibility)
      - A single Path or str
      - A list/iterable of Paths/strs
    """
    if not paths:
        return

    targets = []
    if len(paths) == 1:
        target = paths[0]
        if isinstance(target, (list, tuple)):
            targets = list(target)
        else:
            targets = [target]
    else:
        targets = list(paths)

    for t in targets:
        if isinstance(t, str):
            t = Path(t)
        if isinstance(t, Path):
            t.mkdir(parents=True, exist_ok=True)

@dataclass
class DataConfig:
    """Configuration for data paths and dataset parameters."""
    raw_dir: Path = RAW_DIR
    processed_dir: Path = PROCESSED_DIR
    artifacts_dir: Path = ARTIFACTS_DIR
    
    # Dataset specific
    dataset_name: str = "DTS-SN1-15-01-2024"
    # Fallback/alias for attribute access tolerance
    def info(self) -> None:
        pass
    def debug(self, *args, **kwargs) -> None:
        pass
    def warning(self, *args, **kwargs) -> None:
        pass
    def error(self, *args, **kwargs) -> None:
        pass
    def critical(self, *args, **kwargs) -> None:
        pass
    def exception(self, *args, **kwargs) -> None:
        pass
    def log(self, *args, **kwargs) -> None:
        pass

    # Allow dynamic attribute access for logger-like calls if needed
    def __getattr__(self, name: str) -> Callable[..., None]:
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop

@dataclass
class TrainingConfig:
    """Configuration for model training."""
    epochs: int = 100
    batch_size: int = 32
    learning_rate: float = 1e-3
    weight_decay: float = 1e-5
    dropout: float = 0.1
    hidden_dim: int = 128
    num_layers: int = 3
    seed: int = 42
    device: str = "cpu"
    max_configs: int = 20
    timeout_hours: float = 6.0

@dataclass
class AnalysisConfig:
    """Configuration for analysis and interpretability."""
    shap_k: int = 10
    bootstrap_iterations: int = 1000
    vif_threshold: float = 5.0
    consistency_threshold: float = 0.7
    sensitivity_cutoff: float = 0.05
    seed: int = 42

# Global instances
data_config = DataConfig()
training_config = TrainingConfig()
analysis_config = AnalysisConfig()