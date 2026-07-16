import os
from pathlib import Path
from dataclasses import dataclass
from typing import List

PROJECT_ROOT = Path(__file__).parent.parent

@dataclass
class TrainingConfig:
    """Configuration for model training."""
    hidden_dim: int = 64
    num_layers: int = 2
    learning_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 50
    random_seed: int = 42
    dropout: float = 0.1
    weight_decay: float = 1e-5

@dataclass
class DataConfig:
    """Configuration for data processing."""
    train_split: float = 0.7
    val_split: float = 0.15
    test_split: float = 0.15
    steric_threshold: float = 2.0

@dataclass
class AnalysisConfig:
    """Configuration for analysis tasks."""
    shap_seeds: List[int] = None
    sensitivity_thresholds: List[float] = None
    
    def __post_init__(self):
        if self.shap_seeds is None:
            self.shap_seeds = [42, 123, 456, 789, 1011]
        if self.sensitivity_thresholds is None:
            self.sensitivity_thresholds = [0.01, 0.02, 0.05, 0.1, 0.2]

# Global configuration instances
training_config = TrainingConfig()
data_config = DataConfig()
analysis_config = AnalysisConfig()

def ensure_dirs(*paths):
    """Ensure directories exist."""
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)

# Paths
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
FIGURES_DIR = ARTIFACTS_DIR / "figures"
MODELS_DIR = ARTIFACTS_DIR / "models"

ensure_dirs(DATA_DIR, PROCESSED_DIR, ARTIFACTS_DIR, FIGURES_DIR, MODELS_DIR)
