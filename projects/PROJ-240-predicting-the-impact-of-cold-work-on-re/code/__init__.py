"""
Initialization file for the code package.

This package contains the core implementation for the llmXive automated science pipeline
focused on predicting the impact of cold work on recrystallization kinetics in aluminum alloys.

Public API:
- config: Configuration loading and environment management
- create_artifact_dirs: Directory structure creation
- engineer: Feature engineering and interaction calculations
- finalize_dataset: Final dataset preparation
- generate_metrics_report: Metrics and report generation
- generate_synthetic: Synthetic data generation (for baseline only)
- ingest: Data ingestion, validation, and preprocessing
- main: Pipeline orchestration
- setup_data_dirs: Data directory setup
- setup_project_structure: Project structure initialization
- train: Model training and evaluation
- utils: Utility functions for data processing
"""

# Explicitly expose package version and main entry points
__version__ = "0.1.0"
__author__ = "llmXive Research Team"

# Import key functions for convenient access
from .main import run_all, main
from .config import get_config_value, get_project_root
from .create_artifact_dirs import main as create_dirs
from .setup_project_structure import main as setup_project
