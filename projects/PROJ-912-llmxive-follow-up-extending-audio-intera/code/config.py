"""
Global configuration for llmXive.
Includes PathConfig, SeedConfig, ModelConfig, etc.
"""
import os
import json
import yaml
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path

@dataclass
class PathConfig:
    """Configuration for file paths."""
    # Base paths
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    code_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent)
    data_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data")
    processed_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "processed")
    state_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "state")
    logs_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "logs")
    
    # Derived paths
    def __post_init__(self):
        # Ensure directories exist
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)

    # Added for compatibility with logger.py and other modules that expect logs_dir
    # This ensures that if any script accesses .logs_dir, it works.
    # The dataclass already defines it, but if it was missing in a previous version,
    # this ensures it's present.

@dataclass
class SeedConfig:
    seed: int = 42
    deterministic: bool = True

@dataclass
class ModelConfig:
    teacher_model_id: str = "facebook/wav2vec2-base-960h"
    student_precision: List[str] = field(default_factory=lambda: ["fp32", "int8", "int4"])
    pruning_ratios: List[float] = field(default_factory=lambda: [0.1, 0.2, 0.3])

@dataclass
class ResourceConfig:
    max_ram_gb: float = 7.0
    max_cores: int = 2
    max_time_hours: float = 6.0

@dataclass
class PruningConfig:
    ratios: List[float] = field(default_factory=lambda: [0.1, 0.2, 0.3])
    method: str = "l1_unstructured"

@dataclass
class DatasetConfig:
    name: str = "esc50"
    split: str = "train"
    streaming: bool = True
    subtle_threshold_freq: float = 8000.0
    subtle_threshold_amp: float = -40.0

@dataclass
class DistillationConfig:
    alpha: float = 0.5
    temp: float = 4.0

@dataclass
class EvaluationConfig:
    step_change_threshold: float = 0.10
    weights_score: List[float] = field(default_factory=lambda: [0.5, 0.5])

@dataclass
class Config:
    paths: PathConfig = field(default_factory=PathConfig)
    seeds: SeedConfig = field(default_factory=SeedConfig)
    models: ModelConfig = field(default_factory=ModelConfig)
    resources: ResourceConfig = field(default_factory=ResourceConfig)
    pruning: PruningConfig = field(default_factory=PruningConfig)
    datasets: DatasetConfig = field(default_factory=DatasetConfig)
    distillation: DistillationConfig = field(default_factory=DistillationConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)

def set_seed(seed: int):
    import random
    import numpy as np
    import torch
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def get_pruning_ratios() -> List[float]:
    return Config().pruning.ratios

def get_teacher_model_id() -> str:
    return Config().models.teacher_model_id

def get_resource_limits() -> Dict[str, float]:
    cfg = Config().resources
    return {
        "max_ram_gb": cfg.max_ram_gb,
        "max_cores": cfg.max_cores,
        "max_time_hours": cfg.max_time_hours
    }

def get_distillation_params() -> Dict[str, float]:
    cfg = Config().distillation
    return {
        "alpha": cfg.alpha,
        "temp": cfg.temp
    }

def get_path_config() -> PathConfig:
    return Config().paths

def get_dataset_config() -> DatasetConfig:
    return Config().datasets

def get_evaluation_config() -> EvaluationConfig:
    return Config().evaluation