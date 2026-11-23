"""
Global configuration for llmXive.
Includes PathConfig, SeedConfig, ModelConfig, etc.
Implements config generator/loader (T004c).
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
    
    # Explicitly defined attributes as per task requirements
    # Seeds, paths, model aliases, resource limits, pruning ratios schema
    # threshold values for step-change detection, KD_ALPHA, KD_TEMP
    # EQUAL_WEIGHTS (defined inline), freeze_heads, prune_ffn_layers
    
    # Step change threshold (from EvaluationConfig but exposed here for direct access)
    STEP_CHANGE_THRESHOLD: float = 0.10
    
    # Pruning ratios (from PruningConfig but exposed here)
    PRUNING_RATIOS: List[float] = field(default_factory=lambda: [0.1, 0.2, 0.3])
    
    # Knowledge Distillation parameters
    KD_ALPHA: float = 0.5
    KD_TEMP: float = 4.0
    
    # Weights for score calculation (from EvaluationConfig but exposed here)
    WEIGHTS_SCORE: List[float] = field(default_factory=lambda: [0.5, 0.5])
    
    # Equal weights scalar (default)
    EQUAL_WEIGHTS: float = 0.5
    
    # Freeze heads configuration (list of head indices to freeze)
    freeze_heads: List[int] = field(default_factory=lambda: [0, 1])
    
    # Prune FFN layers configuration (list of layer indices to prune)
    prune_ffn_layers: List[int] = field(default_factory=lambda: [])

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

def load_or_generate_config() -> Config:
    """
    Implements T004c: Config generator/loader.
    
    1) Reads `data/processed/config.yaml` if it exists.
    2) If missing, generates `data/processed/config.yaml` with the required schema
       (pruning_ratios, kd_alpha, kd_temp, weights_score) using defaults from T004b.
       This behavior satisfies the "deferred" clause in FR-001/SC-001 to enable
       staged execution without crashing.
    3) Loads these values into the Config class.
    4) Error Handling: If the file is present but malformed, raises ValueError.
    """
    config_path = Path(__file__).resolve().parent.parent / "data" / "processed" / "config.yaml"
    
    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Default values from T004b
    defaults = {
        "pruning_ratios": [0.1, 0.2, 0.3],
        "kd_alpha": 0.5,
        "kd_temp": 4.0,
        "weights_score": [0.5, 0.5]
    }
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                loaded_data = yaml.safe_load(f)
            
            if loaded_data is None:
                raise ValueError("Config file is empty.")
            
            if not isinstance(loaded_data, dict):
                raise ValueError("Config file must contain a YAML mapping.")
            
            # Validate required keys exist
            required_keys = ["pruning_ratios", "kd_alpha", "kd_temp", "weights_score"]
            missing_keys = [k for k in required_keys if k not in loaded_data]
            if missing_keys:
                raise ValueError(f"Config file missing required keys: {missing_keys}")
            
            # Type validation
            if not isinstance(loaded_data["pruning_ratios"], list):
                raise ValueError("pruning_ratios must be a list.")
            if not isinstance(loaded_data["kd_alpha"], (int, float)):
                raise ValueError("kd_alpha must be a number.")
            if not isinstance(loaded_data["kd_temp"], (int, float)):
                raise ValueError("kd_temp must be a number.")
            if not isinstance(loaded_data["weights_score"], list):
                raise ValueError("weights_score must be a list.")
            
            # Merge loaded config with defaults for other fields
            merged_config = {**defaults, **loaded_data}
            
        except yaml.YAMLError as e:
            raise ValueError(f"Config file is malformed YAML: {e}")
        except Exception as e:
            raise ValueError(f"Error reading config file: {e}")
    else:
        # Generate config file
        merged_config = defaults
        try:
            with open(config_path, 'w') as f:
                yaml.dump(merged_config, f, default_flow_style=False)
        except Exception as e:
            raise RuntimeError(f"Failed to generate default config file: {e}")
    
    # Update Config class attributes with loaded/generated values
    cfg = Config()
    cfg.PRUNING_RATIOS = merged_config["pruning_ratios"]
    cfg.KD_ALPHA = merged_config["kd_alpha"]
    cfg.KD_TEMP = merged_config["kd_temp"]
    cfg.WEIGHTS_SCORE = merged_config["weights_score"]
    
    return cfg