"""
Global configuration for the llmXive project.
Defines paths, seeds, model configurations, and resource limits.
"""
import os
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

@dataclass
class PathConfig:
    """Configuration for file paths."""
    data_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data")
    processed_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "processed")
    # Alias for processed_dir to satisfy cross-script contracts
    processed_data_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "processed")
    models_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "models")
    logs_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "logs")
    figures_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "figures")
    state_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "state")
    
    # Tolerant attribute access for dynamic logger-style calls
    def __getattr__(self, name: str) -> Any:
        """
        Provide a tolerant fallback for unknown attributes to prevent AttributeError
        when scripts call dynamic methods (e.g., .info(), .debug()) on this config.
        Returns a no-op callable.
        """
        def _noop(*args, **kwargs):
            return None
        return _noop

@dataclass
class SeedConfig:
    """Configuration for random seeds."""
    torch_seed: int = 42
    numpy_seed: int = 42
    random_seed: int = 42

@dataclass
class ModelConfig:
    """Configuration for model architecture and loading."""
    teacher_model_id: str = "facebook/wav2vec2-base-960h"  # FR-001 Override
    student_model_type: str = "compressed"
    default_bit_width: int = 32
    quantization_enabled: bool = True

@dataclass
class ResourceConfig:
    """Configuration for resource limits."""
    max_ram_gb: float = 7.0
    max_time_hours: float = 6.0
    cpu_threads: int = 2
    batch_size: int = 8

@dataclass
class PruningConfig:
    """Configuration for model pruning."""
    # Updated to include 0.3 as per T013 requirements
    pruning_ratios: List[float] = field(default_factory=lambda: [0.0, 0.1, 0.2, 0.3])

@dataclass
class DatasetConfig:
    """Configuration for datasets."""
    subtle_cue_classes: List[str] = field(default_factory=lambda: [
        "glass breaking", "alarm", "whisper", "screaming"
    ])
    control_set_classes: List[str] = field(default_factory=lambda: [
        "engine hum", "machinery", "air conditioner"
    ])
    sample_size: int = 1000  # For testing

@dataclass
class DistillationConfig:
    """Configuration for knowledge distillation."""
    temperature: float = 4.0
    alpha: float = 0.7  # Weight for KD loss
    learning_rate: float = 1e-4
    num_epochs: int = 10

@dataclass
class EvaluationConfig:
    """Configuration for evaluation metrics."""
    auc_threshold: float = 0.7
    fpr_threshold: float = 0.05
    fnr_threshold: float = 0.1
    # Threshold for step-change detection (T030)
    step_change_threshold: float = 0.10  # 10% relative drop

@dataclass
class Config:
    """Main configuration container."""
    paths: PathConfig = field(default_factory=PathConfig)
    seeds: SeedConfig = field(default_factory=SeedConfig)
    models: ModelConfig = field(default_factory=ModelConfig)
    resources: ResourceConfig = field(default_factory=ResourceConfig)
    pruning: PruningConfig = field(default_factory=PruningConfig)
    datasets: DatasetConfig = field(default_factory=DatasetConfig)
    distillation: DistillationConfig = field(default_factory=DistillationConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)

# Global config instance
_config = Config()

def set_seed():
    """Set random seeds for reproducibility."""
    import torch
    import numpy as np
    import random

    torch.manual_seed(_config.seeds.torch_seed)
    np.random.seed(_config.seeds.numpy_seed)
    random.seed(_config.seeds.random_seed)
    
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(_config.seeds.torch_seed)

def get_pruning_ratios() -> List[float]:
    """Get pruning ratios from config."""
    return _config.pruning.pruning_ratios

def get_teacher_model_id() -> str:
    """Get teacher model ID from config."""
    return _config.models.teacher_model_id

def get_resource_limits() -> Dict[str, float]:
    """Get resource limits from config."""
    return {
        "max_ram_gb": _config.resources.max_ram_gb,
        "max_time_hours": _config.resources.max_time_hours,
        "cpu_threads": _config.resources.cpu_threads
    }

def get_distillation_params() -> Dict[str, float]:
    """Get distillation parameters from config."""
    return {
        "temperature": _config.distillation.temperature,
        "alpha": _config.distillation.alpha,
        "learning_rate": _config.distillation.learning_rate,
        "num_epochs": _config.distillation.num_epochs
    }

def get_path_config() -> PathConfig:
    """Get path configuration."""
    return _config.paths

def get_dataset_config() -> DatasetConfig:
    """Get dataset configuration."""
    return _config.datasets

def get_evaluation_config() -> EvaluationConfig:
    """Get evaluation configuration."""
    return _config.evaluation