import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import json

@dataclass
class DatasetConfig:
    dataset_id: str = "ds000030"
    base_url: str = "https://openneuro.org/datasets/"
    download_dir: str = "data/raw"

@dataclass
class PreprocessingConfig:
    fmriprep_version: str = "20.2.7"
    output_space: str = "MNI152NLin2009cAsym"
    float32: bool = True
    batch_size: int = 10

@dataclass
class CentralityConfig:
    atlas: str = "aal3"
    vif_threshold: float = 5.0
    fixed_region_indices: list = field(default_factory=lambda: list(range(1, 11)))
    regional_analysis_flag: bool = False

@dataclass
class RegressionConfig:
    regional_analysis_flag: bool = False
    global_model_pvalue_threshold: float = 0.05

@dataclass
class OutputPaths:
    raw_data: str = "data/raw"
    processed_data: str = "data/processed"
    artifacts: str = "data/artifacts"
    figures: str = "figures"
    connectivity_metrics: str = "data/processed/connectivity"
    centrality_raw_metrics: str = "data/processed/centrality/subject_id_metrics.csv"
    centrality_global_scores: str = "data/processed/centrality/global_scores.csv"
    fd_mean: str = "data/processed/behavioral/fd_mean.csv"
    model_predictors: str = "data/processed/centrality/model_predictors.csv"
    linear_model_summary: str = "data/processed/regression/linear_model_summary.csv"
    regional_pvalues: str = "data/processed/regression/regional_pvalues.csv"
    null_residuals: str = "data/processed/validation/null_residuals.csv"
    permutation_results: str = "data/processed/validation/permutation_results.json"
    cv_results: str = "data/processed/validation/cv_results.json"
    fdr_corrected_pvalues: str = "data/processed/validation/fdr_corrected_pvalues.csv"

@dataclass
class Config:
    dataset: DatasetConfig = field(default_factory=DatasetConfig)
    preprocessing: PreprocessingConfig = field(default_factory=PreprocessingConfig)
    centrality: CentralityConfig = field(default_factory=CentralityConfig)
    regression: RegressionConfig = field(default_factory=RegressionConfig)
    output_paths: OutputPaths = field(default_factory=OutputPaths)

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

def get_output_paths() -> Dict[str, str]:
    paths = get_config().output_paths
    return {
        "raw_data": paths.raw_data,
        "processed_data": paths.processed_data,
        "artifacts": paths.artifacts,
        "figures": paths.figures,
        "connectivity_metrics": paths.connectivity_metrics,
        "centrality_raw_metrics": paths.centrality_raw_metrics,
        "centrality_global_scores": paths.centrality_global_scores,
        "fd_mean": paths.fd_mean,
        "model_predictors": paths.model_predictors,
        "linear_model_summary": paths.linear_model_summary,
        "regional_pvalues": paths.regional_pvalues,
        "null_residuals": paths.null_residuals,
        "permutation_results": paths.permutation_results,
        "cv_results": paths.cv_results,
        "fdr_corrected_pvalues": paths.fdr_corrected_pvalues,
    }

def get_fd_threshold() -> float:
    return 0.2

def get_min_retention_rate() -> float:
    return 0.8

def get_power_threshold_n() -> int:
    return 85

def get_vif_threshold() -> float:
    return get_config().centrality.vif_threshold

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
