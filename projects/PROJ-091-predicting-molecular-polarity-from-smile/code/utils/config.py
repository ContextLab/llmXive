import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field, asdict

@dataclass
class ModelConfig:
    seed: int = 42

@dataclass
class PreprocessingConfig:
    batch_size: int = 1000
    drop_threshold: float = 0.05

@dataclass
class TrainingConfig:
    num_leaves: int = 31
    learning_rate: float = 0.05
    n_estimators: int = 100

@dataclass
class PipelineConfig:
    model: ModelConfig = field(default_factory=ModelConfig)
    preprocessing: PreprocessingConfig = field(default_factory=PreprocessingConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)

def load_hyperparameters(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load hyperparameters from YAML or return defaults."""
    defaults = {
        "num_leaves": 31,
        "learning_rate": 0.05,
        "n_estimators": 100
    }
    if config_path and config_path.exists():
        with open(config_path, "r") as f:
            override = yaml.safe_load(f)
            defaults.update(override)
    return defaults

def get_config_summary() -> Dict[str, Any]:
    """Get config summary."""
    return {
        "model": asdict(ModelConfig()),
        "preprocessing": asdict(PreprocessingConfig()),
        "training": asdict(TrainingConfig())
    }
