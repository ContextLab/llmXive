import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import json

@dataclass
class DatasetConfig:
    source: str = "OpenNeuro"
    dataset_id: str = "ds000000"
    download_path: str = "data/raw"
    metadata_file: str = "metadata.csv"

@dataclass
class PreprocessingConfig:
    fmriprep_version: str = "20.2.7"
    output_dir: str = "data/processed/fmriprep"
    float32: bool = True
    batch_size: int = 1

@dataclass
class CentralityConfig:
    top_hubs_n: int = 10
    threshold_fd: float = 0.5
    vif_threshold: float = 5.0
    min_retention_rate: float = 0.80
    power_threshold_n: int = 50

@dataclass
class RegressionConfig:
    pvalue_threshold: float = 0.05
    regional_analysis_flag: bool = True

@dataclass
class OutputPaths:
    base_dir: str = "data/processed"
    behavioral_dir: str = "data/processed/behavioral"
    centrality_dir: str = "data/processed/centrality"
    regression_dir: str = "data/processed/regression"
    validation_dir: str = "data/processed/validation"
    logs_dir: str = "data/processed/logs"

@dataclass
class Config:
    dataset: DatasetConfig = field(default_factory=DatasetConfig)
    preprocessing: PreprocessingConfig = field(default_factory=PreprocessingConfig)
    centrality: CentralityConfig = field(default_factory=CentralityConfig)
    regression: RegressionConfig = field(default_factory=RegressionConfig)
    output: OutputPaths = field(default_factory=OutputPaths)

_config: Optional[Config] = None

def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config

def reset_config():
    global _config
    _config = None

def get_dataset_config() -> DatasetConfig:
    return get_config().dataset

def get_preprocessing_config() -> PreprocessingConfig:
    return get_config().preprocessing

def get_centrality_config() -> CentralityConfig:
    return get_config().centrality

def get_regression_config() -> RegressionConfig:
    return get_config().regression

def get_output_paths() -> OutputPaths:
    return get_config().output

def get_fd_threshold() -> float:
    return get_config().centrality.threshold_fd

def get_min_retention_rate() -> float:
    return get_config().centrality.min_retention_rate

def get_power_threshold_n() -> int:
    return get_config().centrality.power_threshold_n

def get_vif_threshold() -> float:
    return get_config().centrality.vif_threshold

def load_config_from_file(path: str) -> Config:
    # Placeholder for loading from JSON/YAML
    return get_config()

def save_config_to_file(config: Config, path: str) -> None:
    # Placeholder for saving to JSON/YAML
    pass