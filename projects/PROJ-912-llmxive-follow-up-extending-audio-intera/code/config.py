"""
Global configuration for llmXive Audio Interaction Model.

Contains all configuration classes and utility functions for seeds,
paths, model aliases, resource limits, and hyperparameters.
"""
import os
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path

@dataclass
class PathConfig:
    """Configuration for file paths."""
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    code_dir: Path = field(default_factory=lambda: Path(__file__).parent)
    data_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "data")
    processed_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "data" / "processed")
    state_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "state")
    figures_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "figures")
    
    # Aliases for compatibility with various callers
    @property
    def processed_data_dir(self) -> Path:
        """Alias for processed_dir."""
        return self.processed_dir

@dataclass
class SeedConfig:
    """Configuration for random seeds."""
    torch_seed: int = 42
    numpy_seed: int = 42
    python_seed: int = 42
    random_seed: int = 42

@dataclass
class ModelConfig:
    """Configuration for models."""
    teacher_model_id: str = "facebook/wav2vec2-base-960h"
    student_model_id: str = "facebook/wav2vec2-base-960h"
    hidden_size: int = 768
    num_attention_heads: int = 12
    num_hidden_layers: int = 12

@dataclass
class ResourceConfig:
    """Configuration for resource limits."""
    max_ram_gb: float = 7.0
    max_cores: int = 2
    max_time_hours: float = 6.0
    batch_size: int = 8
    use_cpu_only: bool = True

@dataclass
class PruningConfig:
    """Configuration for pruning."""
    pruning_ratios: List[float] = field(default_factory=lambda: [0.1, 0.2, 0.3])
    pruning_method: str = "magnitude"

@dataclass
class DatasetConfig:
    """Configuration for datasets."""
    dataset_name: str = "esc50"
    subtle_cue_threshold_db: float = -40.0
    subtle_cue_threshold_hz: float = 8000.0
    control_set_classes: List[int] = field(default_factory=lambda: [0, 1, 2])

@dataclass
class DistillationConfig:
    """Configuration for knowledge distillation."""
    kd_alpha: float = 0.5
    kd_temp: float = 4.0
    learning_rate: float = 1e-4
    num_epochs: int = 10

@dataclass
class EvaluationConfig:
    """Configuration for evaluation."""
    thresholds: List[float] = field(default_factory=lambda: [0.01, 0.05, 0.1])
    breaking_point_threshold: float = 0.1  # 10% drop

class Config:
    """Main configuration container."""
    def __init__(self):
        self.paths = PathConfig()
        self.seeds = SeedConfig()
        self.models = ModelConfig()
        self.resources = ResourceConfig()
        self.pruning = PruningConfig()
        self.datasets = DatasetConfig()
        self.distillation = DistillationConfig()
        self.evaluation = EvaluationConfig()

def set_seed(seed: int = 42):
    """Set all random seeds."""
    import random
    import numpy as np
    import torch
    
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def get_pruning_ratios() -> List[float]:
    """Get pruning ratios from config."""
    return Config().pruning.pruning_ratios

def get_teacher_model_id() -> str:
    """Get teacher model ID from config."""
    return Config().models.teacher_model_id

def get_resource_limits() -> ResourceConfig:
    """Get resource limits from config."""
    return Config().resources

def get_distillation_params() -> Dict[str, float]:
    """Get distillation parameters from config."""
    cfg = Config().distillation
    return {
        'kd_alpha': cfg.kd_alpha,
        'kd_temp': cfg.kd_temp,
        'learning_rate': cfg.learning_rate,
        'num_epochs': cfg.num_epochs
    }

def get_path_config() -> PathConfig:
    """Get path configuration."""
    return Config().paths

def get_dataset_config() -> DatasetConfig:
    """Get dataset configuration."""
    return Config().datasets

def get_evaluation_config() -> EvaluationConfig:
    """Get evaluation configuration."""
    return Config().evaluation

# For backward compatibility
path_config = get_path_config()
resource_limits = get_resource_limits()
distillation_params = get_distillation_params()