"""
Configuration management for the network centrality pipeline.
Includes optimization settings for memory efficiency.
"""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import json

@dataclass
class DatasetConfig:
    """Configuration for dataset sources and paths."""
    openneuro_dataset_id: str = "ds004253"
    raw_data_dir: str = "data/raw"
    processed_data_dir: str = "data/processed"
    artifacts_dir: str = "data/artifacts"
    download_timeout: int = 3600

@dataclass
class PreprocessingConfig:
    """Configuration for fMRIPrep preprocessing."""
    fmriprep_version: str = "23.1.0"
    float32_conversion: bool = True
    batch_size: int = 5
    memory_limit_gb: float = 14.0
    n_jobs: int = -1
    fd_threshold: float = 0.5
    min_retention_rate: float = 0.8

@dataclass
class CentralityConfig:
    """Configuration for centrality calculations."""
    atlas_name: str = "AAL3"
    atlas_file: str = "aal3.nii.gz"
    centrality_metrics: list = field(default_factory=lambda: ["degree", "betweenness", "eigenvector"])
    batch_processing: bool = True
    batch_size: int = 100
    vif_threshold: float = 5.0

@dataclass
class RegressionConfig:
    """Configuration for regression models."""
    model_type: str = "linear"
    include_intercept: bool = True
    regional_analysis_flag: bool = False
    global_model_pvalue_threshold: float = 0.05
    permutation_shuffles: int = 1000
    permutation_seed: int = 42
    cv_folds: int = 5
    cv_seed: int = 42

@dataclass
class OutputPaths:
    """Configuration for output file paths."""
    behavioral_scores: str = "data/processed/behavioral/subject_scores.csv"
    retention_metrics: str = "data/processed/behavioral/retention_metrics.json"
    centrality_metrics: str = "data/processed/centrality/subject_id_metrics.csv"
    global_scores: str = "data/processed/centrality/global_scores.csv"
    mean_fd: str = "data/processed/behavioral/fd_mean.csv"
    vif_values: str = "data/processed/centrality/vif_values.csv"
    model_predictors: str = "data/processed/centrality/model_predictors.csv"
    linear_model_summary: str = "data/processed/regression/linear_model_summary.csv"
    null_residuals: str = "data/processed/validation/null_residuals.csv"
    baseline_r2: str = "data/processed/validation/baseline_r2.json"
    nonlinearity_check: str = "data/processed/regression/nonlinearity_check.csv"
    scatter_plot: str = "figures/regression_scatter.png"
    null_distribution: str = "data/processed/validation/null_distribution.csv"
    permutation_results: str = "data/processed/validation/permutation_results.json"
    cv_results: str = "data/processed/validation/cv_results.json"
    exclusion_log: str = "data/processed/logs/exclusion_log.csv"
    reproducibility_report: str = "data/artifacts/reproducibility_report.json"

@dataclass
class Config:
    """Main configuration container."""
    dataset: DatasetConfig = field(default_factory=DatasetConfig)
    preprocessing: PreprocessingConfig = field(default_factory=PreprocessingConfig)
    centrality: CentralityConfig = field(default_factory=CentralityConfig)
    regression: RegressionConfig = field(default_factory=RegressionConfig)
    output: OutputPaths = field(default_factory=OutputPaths)

# Global config instance
_config: Optional[Config] = None

def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config

def reset_config():
    """Reset the global configuration to defaults."""
    global _config
    _config = None

def get_dataset_config() -> DatasetConfig:
    """Get dataset configuration."""
    return get_config().dataset

def get_preprocessing_config() -> PreprocessingConfig:
    """Get preprocessing configuration."""
    return get_config().preprocessing

def get_centrality_config() -> CentralityConfig:
    """Get centrality configuration."""
    return get_config().centrality

def get_regression_config() -> RegressionConfig:
    """Get regression configuration."""
    return get_config().regression

def get_output_paths() -> OutputPaths:
    """Get output paths configuration."""
    return get_config().output

def get_fd_threshold() -> float:
    """Get FD threshold for subject exclusion."""
    return get_config().preprocessing.fd_threshold

def get_min_retention_rate() -> float:
    """Get minimum retention rate threshold."""
    return get_config().preprocessing.min_retention_rate

def get_power_threshold_n() -> int:
    """Get power threshold for sample size warning."""
    return 85

def get_vif_threshold() -> float:
    """Get VIF threshold for multicollinearity check."""
    return get_config().centrality.vif_threshold

def get_permutation_shuffles() -> int:
    """Get number of permutation shuffles."""
    return get_config().regression.permutation_shuffles

def get_permutation_seed() -> int:
    """Get random seed for permutation test."""
    return get_config().regression.permutation_seed

def get_cv_folds() -> int:
    """Get number of cross-validation folds."""
    return get_config().regression.cv_folds

def get_cv_seed() -> int:
    """Get random seed for cross-validation."""
    return get_config().regression.cv_seed

def get_regional_analysis_flag() -> bool:
    """Get flag for regional analysis."""
    return get_config().regression.regional_analysis_flag

def get_global_model_pvalue_threshold() -> float:
    """Get p-value threshold for global model."""
    return get_config().regression.global_model_pvalue_threshold

def load_config_from_file(config_path: str) -> Config:
    """Load configuration from a JSON file."""
    with open(config_path, 'r') as f:
        config_dict = json.load(f)
    
    config = Config()
    if 'dataset' in config_dict:
        config.dataset = DatasetConfig(**config_dict['dataset'])
    if 'preprocessing' in config_dict:
        config.preprocessing = PreprocessingConfig(**config_dict['preprocessing'])
    if 'centrality' in config_dict:
        config.centrality = CentralityConfig(**config_dict['centrality'])
    if 'regression' in config_dict:
        config.regression = RegressionConfig(**config_dict['regression'])
    if 'output' in config_dict:
        config.output = OutputPaths(**config_dict['output'])
        
    return config

def save_config_to_file(config: Config, config_path: str):
    """Save configuration to a JSON file."""
    config_dict = {
        'dataset': config.dataset.__dict__,
        'preprocessing': config.preprocessing.__dict__,
        'centrality': config.centrality.__dict__,
        'regression': config.regression.__dict__,
        'output': config.output.__dict__
    }
    
    with open(config_path, 'w') as f:
        json.dump(config_dict, f, indent=2)

def main():
    """Main entry point for configuration module."""
    config = get_config()
    print("Current configuration:")
    print(f"  Dataset ID: {config.dataset.openneuro_dataset_id}")
    print(f"  Float32 conversion: {config.preprocessing.float32_conversion}")
    print(f"  Batch size: {config.centrality.batch_size}")
    print(f"  VIF threshold: {config.centrality.vif_threshold}")

if __name__ == "__main__":
    main()
