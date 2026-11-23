"""
Configuration module for llmXive research pipeline.

Handles environment variables, random seed management, and project-specific constants
including city mappings and file paths.
"""
import os
import random
import numpy as np
from pathlib import Path
from typing import Dict, List, Set, Optional, Any


# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data Directories
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
ANALYSIS_DATA_DIR = PROJECT_ROOT / "data" / "analysis"
FIGURES_DIR = PROJECT_ROOT / "data" / "figures"
LOGS_DIR = PROJECT_ROOT / "logs"

# Model Directories
MODELS_DIR = PROJECT_ROOT / "models"

# Output Files
GROUND_TRUTH_FILE = RAW_DATA_DIR / "transitlm_ground_truth.json"
FILTERED_ROUTES_FILE = PROCESSED_DATA_DIR / "city_filtered_routes.jsonl"
VOBAB_RESTRICTED_ROUTES_FILE = PROCESSED_DATA_DIR / "vocab_restricted_routes.jsonl"
STRATIFIED_ROUTES_FILE = PROCESSED_DATA_DIR / "stratified_routes.parquet"
ADJACENCY_GRAPH_FILE = PROCESSED_DATA_DIR / "adjacency_graph.pkl"
ADJACENCY_INDEX_FILE = PROCESSED_DATA_DIR / "adjacency_index.pkl"
ROUTE_COMPLEXITY_METRICS_FILE = ANALYSIS_DATA_DIR / "route_complexity_metrics.json"
RAW_INFLECTION_DATA_FILE = ANALYSIS_DATA_DIR / "raw_inflection_data.json"
FINAL_INFLECTION_REPORT_FILE = ANALYSIS_DATA_DIR / "final_inflection_report.json"
SURVIVAL_DATA_FILE = ANALYSIS_DATA_DIR / "survival_data.json"
SURVIVAL_CURVES_FILE = ANALYSIS_DATA_DIR / "survival_curves.pdf"
STATISTICAL_REPORT_FILE = ANALYSIS_DATA_DIR / "statistical_report.json"
PROFILING_REPORT_FILE = ANALYSIS_DATA_DIR / "profiling_report.json"
PERFORMANCE_REPORT_FILE = ANALYSIS_DATA_DIR / "performance_report.json"
EVALUATION_LOG_FILE = LOGS_DIR / "evaluation.log"

# Graph Validation
GRAPH_VALIDATION_REPORT_FILE = PROCESSED_DATA_DIR / "graph_validation_report.json"

# Target Cities (Chinese cities for the study)
TARGET_CITIES: Set[str] = {
    "Beijing",
    "Shanghai",
    "Guangzhou",
    "Shenzhen"
}

# Station Vocabulary Restriction
TOP_N_STATIONS: int = 1000  # Top-N stations to keep in vocabulary

# Route Stratification Thresholds
SHORT_ROUTE_MAX_STOPS: int = 14       # < 15 stops
MEDIUM_ROUTE_MAX_STOPS: int = 30      # 15-30 stops
# Long routes are > 30 stops

# Evaluation Thresholds
VALIDITY_DROP_THRESHOLD: float = 0.15  # 15% absolute drop
SIGNIFICANCE_ALPHA: float = 0.05       # p-value threshold

# Topological Complexity
TOP_N_NEIGHBORS: int = 50              # Top-N neighbors for adjacency index

# Random Seeds
DEFAULT_SEED: int = 42

# Environment Configuration Keys
ENV_RANDOM_SEED: str = "LLMXIVE_RANDOM_SEED"
ENV_DATA_ROOT: str = "LLMXIVE_DATA_ROOT"
ENV_LOG_LEVEL: str = "LLMXIVE_LOG_LEVEL"


class Config:
    """
    Configuration container class.
    Holds all project-wide constants and runtime settings.
    """
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.raw_data_dir = RAW_DATA_DIR
        self.processed_data_dir = PROCESSED_DATA_DIR
        self.analysis_data_dir = ANALYSIS_DATA_DIR
        self.figures_dir = FIGURES_DIR
        self.logs_dir = LOGS_DIR
        self.models_dir = MODELS_DIR

        self.ground_truth_file = GROUND_TRUTH_FILE
        self.filtered_routes_file = FILTERED_ROUTES_FILE
        self.vocab_restricted_routes_file = VOBAB_RESTRICTED_ROUTES_FILE
        self.stratified_routes_file = STRATIFIED_ROUTES_FILE
        self.adjacency_graph_file = ADJACENCY_GRAPH_FILE
        self.adjacency_index_file = ADJACENCY_INDEX_FILE
        self.route_complexity_metrics_file = ROUTE_COMPLEXITY_METRICS_FILE
        self.raw_inflection_data_file = RAW_INFLECTION_DATA_FILE
        self.final_inflection_report_file = FINAL_INFLECTION_REPORT_FILE
        self.survival_data_file = SURVIVAL_DATA_FILE
        self.survival_curves_file = SURVIVAL_CURVES_FILE
        self.statistical_report_file = STATISTICAL_REPORT_FILE
        self.profiling_report_file = PROFILING_REPORT_FILE
        self.performance_report_file = PERFORMANCE_REPORT_FILE
        self.evaluation_log_file = EVALUATION_LOG_FILE
        self.graph_validation_report_file = GRAPH_VALIDATION_REPORT_FILE

        self.target_cities = TARGET_CITIES
        self.top_n_stations = TOP_N_STATIONS
        self.short_route_max_stops = SHORT_ROUTE_MAX_STOPS
        self.medium_route_max_stops = MEDIUM_ROUTE_MAX_STOPS
        self.validity_drop_threshold = VALIDITY_DROP_THRESHOLD
        self.significance_alpha = SIGNIFICANCE_ALPHA
        self.top_n_neighbors = TOP_N_NEIGHBORS
        self.default_seed = DEFAULT_SEED

    def __repr__(self) -> str:
        return (
            f"Config(project_root={self.project_root}, "
            f"target_cities={self.target_cities}, "
            f"seed={self.default_seed})"
        )


def get_env_config() -> Dict[str, Any]:
    """
    Retrieve configuration from environment variables.
    Falls back to defaults if not set.
    
    Returns:
        Dictionary containing configuration values.
    """
    seed = int(os.getenv(ENV_RANDOM_SEED, DEFAULT_SEED))
    data_root = os.getenv(ENV_DATA_ROOT, str(PROJECT_ROOT))
    log_level = os.getenv(ENV_LOG_LEVEL, "INFO")
    
    return {
        "seed": seed,
        "data_root": data_root,
        "log_level": log_level
    }


def set_global_seed(seed: Optional[int] = None) -> int:
    """
    Set random seeds for reproducibility across Python, NumPy, and PyTorch.
    
    Args:
        seed: Random seed value. If None, uses DEFAULT_SEED or env variable.
    
    Returns:
        The seed value that was set.
    """
    if seed is None:
        seed = int(os.getenv(ENV_RANDOM_SEED, DEFAULT_SEED))
    
    random.seed(seed)
    np.random.seed(seed)
    
    # Try to set torch seed if available
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass  # Torch not installed, continue without it
    
    return seed