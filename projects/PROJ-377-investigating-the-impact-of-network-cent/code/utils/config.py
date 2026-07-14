import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import json

@dataclass
class DatasetConfig:
    dataset_id: str = "ds000030"
    base_url: str = "https://openneuro.org/datasets"
    local_path: Optional[str] = None

@dataclass
class PreprocessingConfig:
    fmriprep_version: str = "20.2.7"
    float32_conversion: bool = True
    batch_size: int = 10
    fd_threshold: float = 0.2
    min_retention_rate: float = 0.80  # T015: 80% retention threshold
    min_subjects: int = 85

@dataclass
class CentralityConfig:
    atlas: str = "AAL3"
    n_nodes: int = 90
    fixed_region_indices: list = field(default_factory=lambda: list(range(1, 11)))  # Indices 1-10
    metrics: list = field(default_factory=lambda: ["degree", "betweenness", "eigenvector"])

@dataclass
class RegressionConfig:
    regional_analysis_flag: bool = False
    global_model_pvalue_threshold: float = 0.05
    vif_threshold: float = 5.0

@dataclass
class OutputPaths:
    raw_data: str = "data/raw"
    processed_fmriprep: str = "data/processed/fmriprep"
    processed_connectivity: str = "data/processed/connectivity"
    processed_centrality: str = "data/processed/centrality"
    processed_behavioral: str = "data/processed/behavioral"
    behavioral_processed: str = "data/processed/behavioral/behavioral_metrics.csv"
    fd_processed: str = "data/processed/behavioral/fd_mean.csv"
    behavioral_final: str = "data/processed/behavioral/final_retained.csv"
    regression_summary: str = "data/processed/regression/linear_model_summary.csv"
    regional_pvalues: str = "data/processed/regression/regional_pvalues.csv"
    validation_results: str = "data/processed/validation"
    artifacts: str = "data/artifacts"

@dataclass
class Config:
    dataset: DatasetConfig = field(default_factory=DatasetConfig)
    preprocessing: PreprocessingConfig = field(default_factory=PreprocessingConfig)
    centrality: CentralityConfig = field(default_factory=CentralityConfig)
    regression: RegressionConfig = field(default_factory=RegressionConfig)
    output: OutputPaths = field(default_factory=OutputPaths)
    _instance: Optional['Config'] = None

# Global config instance
_config: Optional[Config] = None

def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
        # Load from environment or file if available
        env_config_path = os.getenv("LLMXIVE_CONFIG_PATH")
        if env_config_path and os.path.exists(env_config_path):
            with open(env_config_path, 'r') as f:
                loaded = json.load(f)
                # Simple merge (in real app, would validate and map properly)
                if 'preprocessing' in loaded:
                    _config.preprocessing = PreprocessingConfig(**loaded['preprocessing'])
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
    return get_config().preprocessing.fd_threshold

def get_min_retention_rate() -> float:
    # T015: Return the configured minimum retention rate (default 0.80)
    return get_config().preprocessing.min_retention_rate

def get_power_threshold_n() -> int:
    return get_config().preprocessing.min_subjects

def get_vif_threshold() -> float:
    return get_config().regression.vif_threshold

def get_permutation_shuffles() -> int:
    return 1000

def get_permutation_seed() -> int:
    return 42

def get_cv_folds() -> int:
    return 5

def get_fixed_region_indices() -> list:
    return get_config().centrality.fixed_region_indices

def get_regional_analysis_flag() -> bool:
    return get_config().regression.regional_analysis_flag

def get_global_model_pvalue_threshold() -> float:
    return get_config().regression.global_model_pvalue_threshold
