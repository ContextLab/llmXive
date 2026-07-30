"""
PROJ-240: Predicting the Impact of Cold Work on Recrystallization Kinetics in Aluminum Alloys

This package provides the core implementation for ingesting, engineering, 
modeling, and evaluating the impact of cold work on recrystallization kinetics.

Key Modules:
- ingest: Data loading, validation, and cleaning.
- engineer: Feature engineering (interaction terms).
- train: Model training and cross-validation.
- evaluate: Statistical significance testing and SHAP analysis.
- utils: Helper functions, constants, and VIF calculations.
- create_artifact_dirs: Directory setup utilities.
- setup_data_dirs: Data directory setup utilities.
"""

from .create_artifact_dirs import main as create_artifact_dirs_main
from .setup_data_dirs import main as setup_data_dirs_main

__version__ = "0.1.0"
__author__ = "llmXive Research Team"

# Expose main entry points for scaffolding
__all__ = [
    "create_artifact_dirs_main",
    "setup_data_dirs_main",
]