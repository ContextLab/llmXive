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
    # Explicit URL configuration for programmatic access if CLI is not used
    dataset_url: str = "https://openneuro.org/datasets/ds000000"

@dataclass
class PreprocessingConfig:
    fmriprep_version: str = "20.2.7"
    output_dir: str = "data/processed/fmriprep"
    float32: bool = True
    batch_size: int = 1
    # Memory and performance thresholds
    max_memory_gb: float = 16.0
    n_cpus: int = 4

@dataclass
class CentralityConfig:
    top_hubs_n: int = 10
    threshold_fd: float = 0.5
    vif_threshold: float = 5.0
    min_retention_rate: float = 0.80
    power_threshold_n: int = 50
    # Hub selection method: 'data_driven' (FR-002.1) or 'fixed'
    hub_selection_method: str = "data_driven"

@dataclass
class RegressionConfig:
    pvalue_threshold: float = 0.05
    regional_analysis_flag: bool = True
    # Model selection thresholds
    r2_baseline_threshold: float = 0.05
    p_value_fallback_threshold: float = 0.1

@dataclass
class OutputPaths:
    base_dir: str = "data/processed"
    behavioral_dir: str = "data/processed/behavioral"
    centrality_dir: str = "data/processed/centrality"
    regression_dir: str = "data/processed/regression"
    validation_dir: str = "data/processed/validation"
    logs_dir: str = "data/processed/logs"
    figures_dir: str = "data/processed/figures"

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

def get_hub_selection_method() -> str:
    return get_config().centrality.hub_selection_method

def get_r2_baseline_threshold() -> float:
    return get_config().regression.r2_baseline_threshold

def get_p_value_fallback_threshold() -> float:
    return get_config().regression.p_value_fallback_threshold

def load_config_from_file(path: str) -> Config:
    """
    Load configuration from a JSON file.
    If the file does not exist, returns the default config.
    """
    global _config
    if not os.path.exists(path):
        return get_config()

    try:
        with open(path, 'r') as f:
            data = json.load(f)
        
        # Reconstruct dataclasses from dict
        dataset = DatasetConfig(**data.get('dataset', {}))
        preprocessing = PreprocessingConfig(**data.get('preprocessing', {}))
        centrality = CentralityConfig(**data.get('centrality', {}))
        regression = RegressionConfig(**data.get('regression', {}))
        output = OutputPaths(**data.get('output', {}))
        
        _config = Config(
            dataset=dataset,
            preprocessing=preprocessing,
            centrality=centrality,
            regression=regression,
            output=output
        )
        return _config
    except Exception as e:
        # Fallback to defaults if parsing fails, but log the error
        # In a real pipeline, this might raise or halt
        return get_config()

def save_config_to_file(config: Config, path: str) -> None:
    """
    Save the current configuration to a JSON file.
    """
    data = {
        'dataset': config.dataset.__dict__,
        'preprocessing': config.preprocessing.__dict__,
        'centrality': config.centrality.__dict__,
        'regression': config.regression.__dict__,
        'output': config.output.__dict__
    }
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)