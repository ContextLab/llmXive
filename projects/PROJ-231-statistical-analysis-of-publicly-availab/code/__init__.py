"""
llmXive Statistical Analysis Pipeline - Main Package

This package provides tools for statistical analysis of publicly available
climate model output ensembles, including:

- Data ingestion and preprocessing (CMIP6)
- Functional representation via B-splines
- Functional Principal Component Analysis (fPCA)
- Robustness assessment via Leave-One-Out Jackknife

Submodules:
- config: Project configuration and paths
- ingestion: Data download and preprocessing
- basis: B-spline basis expansion and reconstruction
- fpca: Functional PCA implementation
- robustness: LOO Jackknife stability analysis
- visualize: Visualization utilities
- cleanup_utils: Cleanup and refactoring utilities
- refactoring_helpers: Shared helper functions
"""

from .config import get_project_root, get_data_dir, get_artifacts_dir, get_log_dir
from .logging_config import setup_logging, get_logger

__version__ = "1.0.0"
__author__ = "llmXive Research Team"

__all__ = [
    "get_project_root",
    "get_data_dir", 
    "get_artifacts_dir",
    "get_log_dir",
    "setup_logging",
    "get_logger",
]