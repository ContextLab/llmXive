"""
Configuration management for the plant drought tolerance prediction pipeline.

This module centralizes all paths, random seeds, and hyperparameters to ensure
reproducibility and consistent configuration across the project.
"""

import os
from pathlib import Path
from typing import Any, Dict, Final
from dataclasses import dataclass, field

# Project Root
# Assumes code/config.py is at code/config.py, so root is parent of parent
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent

# Directories
DATA_RAW_DIR: Final[Path] = PROJECT_ROOT / "data" / "raw"
DATA_DERIVED_DIR: Final[Path] = PROJECT_ROOT / "data" / "derived"
CODE_DIR: Final[Path] = PROJECT_ROOT / "code"
TESTS_DIR: Final[Path] = PROJECT_ROOT / "tests"
DOCS_DIR: Final[Path] = PROJECT_ROOT / "docs"
STATE_DIR: Final[Path] = PROJECT_ROOT / "state"
CONTRACTS_DIR: Final[Path] = PROJECT_ROOT / "contracts"
RESULTS_DIR: Final[Path] = PROJECT_ROOT / "results"
FIGURES_DIR: Final[Path] = RESULTS_DIR / "figures"

# Random Seed for reproducibility
RANDOM_SEED: Final[int] = 42

# Hyperparameters
@dataclass
class Hyperparameters:
    """Container for model training hyperparameters."""
    
    # PCA
    pca_n_components: int = 3
    
    # Regression Models
    regression_test_size: float = 0.2
    regression_cv_folds: int = 5
    
    # Ridge/Lasso
    alpha_range: list = field(default_factory=lambda: [0.01, 0.1, 1.0, 10.0, 100.0])
    
    # Random Forest Regression
    rf_n_estimators: int = 100
    rf_max_depth: Any = None
    rf_min_samples_leaf: int = 1
    
    # Random Forest Classification
    rf_class_n_estimators: int = 100
    rf_class_max_depth: Any = None
    rf_class_min_samples_leaf: int = 1
    
    # VIF Threshold
    vif_threshold: float = 5.0
    
    # Power Analysis
    power_analysis_min_species: int = 55
    
    # Image Processing
    image_skeleton_connectivity: int = 8
    
    # Multiple Comparison Correction
    correction_method: str = "fdr_bh"  # Benjamini-Hochberg
    
    # Sensitivity Analysis
    sensitivity_threshold_range: list = field(default_factory=lambda: [0.3, 0.4, 0.5, 0.6, 0.7])

HYPERPARAMETERS: Final[Hyperparameters] = Hyperparameters()

# File Paths (Dynamic based on project structure)
RSAMETRICS_CSV: Final[Path] = DATA_DERIVED_DIR / "rsametrics.csv"
PHYLOGENY_TREE_NEWICK: Final[Path] = DATA_DERIVED_DIR / "phylogenetic_tree.newick"
MODEL_RESULTS_CSV: Final[Path] = DATA_DERIVED_DIR / "model_results.csv"
SENSITIVITY_RESULTS_CSV: Final[Path] = DATA_DERIVED_DIR / "sensitivity_sweep_results.csv"
SENSITIVITY_PLOT: Final[Path] = FIGURES_DIR / "sensitivity_curve.png"
POWER_ANALYSIS_REPORT: Final[Path] = STATE_DIR / "power_analysis_report.yaml"
VIF_COMPLIANCE_CHECK: Final[Path] = STATE_DIR / "vif_compliance_check.yaml"
PROXY_DETECTION: Final[Path] = STATE_DIR / "proxy_detection.yaml"
CLASSIFICATION_STATUS: Final[Path] = DATA_DERIVED_DIR / "classification_status.md"
REPORT_FRAMING: Final[Path] = DATA_DERIVED_DIR / "report_framing.md"

# NPPN HuggingFace Repository ID
NPPN_REPO_ID: Final[str] = "nppn/root-phenotyping"

# Environment Variables
TRY_API_KEY_ENV: Final[str] = "TRY_API_KEY"

def ensure_directories() -> None:
    """Create all required project directories if they do not exist."""
    dirs = [
        DATA_RAW_DIR,
        DATA_DERIVED_DIR,
        CODE_DIR,
        TESTS_DIR,
        DOCS_DIR,
        STATE_DIR,
        CONTRACTS_DIR,
        RESULTS_DIR,
        FIGURES_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Ensure directories exist upon import (optional, can be called explicitly)
# ensure_directories() 

def get_config_summary() -> Dict[str, Any]:
    """Return a dictionary summary of the current configuration."""
    return {
        "project_root": str(PROJECT_ROOT),
        "random_seed": RANDOM_SEED,
        "hyperparameters": {
            "pca_n_components": HYPERPARAMETERS.pca_n_components,
            "regression_test_size": HYPERPARAMETERS.regression_test_size,
            "regression_cv_folds": HYPERPARAMETERS.regression_cv_folds,
            "alpha_range": HYPERPARAMETERS.alpha_range,
            "rf_n_estimators": HYPERPARAMETERS.rf_n_estimators,
            "rf_max_depth": HYPERPARAMETERS.rf_max_depth,
            "vif_threshold": HYPERPARAMETERS.vif_threshold,
            "power_analysis_min_species": HYPERPARAMETERS.power_analysis_min_species,
        },
        "key_paths": {
            "rsametrics": str(RSAMETRICS_CSV),
            "phylogeny": str(PHYLOGENY_TREE_NEWICK),
            "model_results": str(MODEL_RESULTS_CSV),
            "sensitivity_results": str(SENSITIVITY_RESULTS_CSV),
            "power_report": str(POWER_ANALYSIS_REPORT),
        }
    }