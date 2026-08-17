"""
Configuration for the SN1 Rate Constant Prediction Project.
"""
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List

# Project root relative to this file
BASE_DIR = Path(__file__).resolve().parent.parent

@dataclass
class DataConfig:
    # Paths
    raw_data_path: Path = BASE_DIR / "data" / "raw" / "sn1_raw.parquet"
    intermediate_data_path: Path = BASE_DIR / "data" / "processed" / "intermediate_sn1.csv"
    cleaned_data_path: Path = BASE_DIR / "data" / "processed" / "cleaned_intermediate.csv"
    descriptors_path: Path = BASE_DIR / "data" / "processed" / "descriptors.csv"
    final_data_path: Path = BASE_DIR / "data" / "processed" / "cleaned_sn1.csv"
    
    # Log paths
    schema_check_log: Path = BASE_DIR / "data" / "processed" / "schema_check.log"
    exclusion_raw_log: Path = BASE_DIR / "data" / "processed" / "exclusion_raw.log"
    clean_log: Path = BASE_DIR / "data" / "processed" / "clean.log"
    exclusion_report_path: Path = BASE_DIR / "data" / "processed" / "exclusion_report.csv"
    
    # Dataset names (HuggingFace)
    dataset_name_1: str = "DTS-SN1-15-01-2024"
    dataset_name_2: str = "SN18-All-20240204"

@dataclass
class TrainingConfig:
    # Model hyperparameters
    hidden_dim: int = 64
    num_layers: int = 3
    dropout: float = 0.1
    learning_rate: float = 1e-3
    batch_size: int = 32
    epochs: int = 50
    seed: int = 42
    
    # Paths
    model_output_dir: Path = BASE_DIR / "artifacts"
    best_model_path: Path = BASE_DIR / "artifacts" / "best_model.pt"
    metrics_path: Path = BASE_DIR / "artifacts" / "metrics.json"
    hyperparameter_log_path: Path = BASE_DIR / "artifacts" / "hyperparameter_search.csv"

@dataclass
class AnalysisConfig:
    # SHAP settings
    shap_sample_size: int = 1000
    
    # Sensitivity settings
    sensitivity_k_range: List[int] = None
    
    def __post_init__(self):
        if self.sensitivity_k_range is None:
            self.sensitivity_k_range = list(range(1, 11))

def ensure_dirs():
    """Create necessary directories for data and artifacts."""
    data_config = DataConfig()
    training_config = TrainingConfig()
    
    dirs = [
        data_config.raw_data_path.parent,
        data_config.intermediate_data_path.parent,
        data_config.cleaned_data_path.parent,
        data_config.descriptors_path.parent,
        data_config.final_data_path.parent,
        data_config.schema_check_log.parent,
        data_config.exclusion_raw_log.parent,
        data_config.clean_log.parent,
        training_config.model_output_dir,
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Instantiation for easy import
data_config = DataConfig()
training_config = TrainingConfig()
analysis_config = AnalysisConfig()
