"""
Configuration management for the Plant Pathogen Host Range Prediction Pipeline.

This module defines all project paths, random seeds, model hyperparameters,
and processing thresholds. It provides a centralized configuration object
to ensure reproducibility and consistency across the pipeline.
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# ========================================================================
# Project Root and Directory Structure
# ========================================================================

class Paths:
    """Centralized path definitions relative to the project root."""
    
    def __init__(self, project_root: Optional[Path] = None):
        if project_root is None:
            # Default to the directory containing this file's parent's parent
            # code/src/config.py -> code -> project_root
            self.project_root = Path(__file__).resolve().parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        # Core directories
        self.code_dir = self.project_root / "code"
        self.data_dir = self.project_root / "data"
        self.tests_dir = self.project_root / "tests"
        self.specs_dir = self.project_root / "specs"
        self.contracts_dir = self.project_root / "contracts"
        
        # Data subdirectories
        self.data_raw_dir = self.data_dir / "raw"
        self.data_processed_dir = self.data_dir / "processed"
        self.data_models_dir = self.data_dir / "models"
        self.data_reports_dir = self.data_dir / "reports"
        
        # Other directories
        self.logs_dir = self.project_root / "logs"
        self.figures_dir = self.data_dir / "figures"
        
        # Ensure directories exist (optional, can be called explicitly)
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Create all required directories if they do not exist."""
        dirs = [
            self.data_raw_dir,
            self.data_processed_dir,
            self.data_models_dir,
            self.data_reports_dir,
            self.logs_dir,
            self.figures_dir,
            self.contracts_dir,
            self.tests_dir,
            self.code_dir,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
    
    def __repr__(self) -> str:
        return f"Paths(project_root={self.project_root})"

# ========================================================================
# Random Seeds for Reproducibility
# ========================================================================

class Seeds:
    """Random seeds for all stochastic processes."""
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.np_seed = seed
        self.sklearn_seed = seed
        self.python_seed = seed
    
    def get_all_seeds(self) -> Dict[str, int]:
        """Return a dictionary of all seed values."""
        return {
            "seed": self.seed,
            "numpy": self.np_seed,
            "sklearn": self.sklearn_seed,
            "python": self.python_seed,
        }

# ========================================================================
# Model Hyperparameters
# ========================================================================

class ModelParams:
    """Hyperparameters for model training and evaluation."""
    
    def __init__(
        self,
        cv_folds: int = 5,
        vif_threshold: float = 5.0,
        l1_penalty_strength: float = 1.0,
        solver: str = "liblinear",
        max_iter: int = 1000,
        n_permutations: int = 100,
        shap_sample_size: int = 1000,
    ):
        self.cv_folds = cv_folds
        self.vif_threshold = vif_threshold
        self.l1_penalty_strength = l1_penalty_strength
        self.solver = solver
        self.max_iter = max_iter
        self.n_permutations = n_permutations
        self.shap_sample_size = shap_sample_size
    
    def __repr__(self) -> str:
        return (
            f"ModelParams(cv_folds={self.cv_folds}, "
            f"vif_threshold={self.vif_threshold})"
        )

# ========================================================================
# Processing Thresholds and Constants
# ========================================================================

class Thresholds:
    """Thresholds for data processing, filtering, and reporting."""
    
    def __init__(
        self,
        min_interactions_per_pathogen: int = 1,
        max_missing_data_ratio: float = 0.2,
        significance_level: float = 0.05,
        fdr_method: str = "benjamini_hochberg",
        host_range_breadth_threshold: float = 0.5,
        zero_interaction_halt: bool = True,
    ):
        self.min_interactions_per_pathogen = min_interactions_per_pathogen
        self.max_missing_data_ratio = max_missing_data_ratio
        self.significance_level = significance_level
        self.fdr_method = fdr_method
        self.host_range_breadth_threshold = host_range_breadth_threshold
        self.zero_interaction_halt = zero_interaction_halt
    
    def __repr__(self) -> str:
        return (
            f"Thresholds(min_interactions={self.min_interactions_per_pathogen}, "
            f"significance={self.significance_level})"
        )

# ========================================================================
# Configuration Loading and Validation
# ========================================================================

def load_config_from_json(config_path: Path) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.
    
    Args:
        config_path: Path to the JSON configuration file.
        
    Returns:
        Dictionary containing the configuration.
        
    Raises:
        FileNotFoundError: If the config file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_seed(seed_override: Optional[int] = None) -> int:
    """
    Get the random seed, optionally overridden by a command-line argument.
    
    Args:
        seed_override: Optional seed value from CLI.
        
    Returns:
        The seed value to use.
    """
    if seed_override is not None:
        return seed_override
    return 42  # Default seed

def validate_paths(paths: Paths) -> bool:
    """
    Validate that all required directories exist.
    
    Args:
        paths: Paths object to validate.
        
    Returns:
        True if all paths are valid, False otherwise.
    """
    required_dirs = [
        paths.data_raw_dir,
        paths.data_processed_dir,
        paths.data_models_dir,
        paths.data_reports_dir,
        paths.logs_dir,
        paths.contracts_dir,
    ]
    
    all_valid = True
    for d in required_dirs:
        if not d.exists():
            print(f"Warning: Directory does not exist: {d}")
            all_valid = False
        elif not d.is_dir():
            print(f"Warning: Path is not a directory: {d}")
            all_valid = False
    
    return all_valid

# ========================================================================
# Default Configuration Instance
# ========================================================================

def get_default_config() -> Dict[str, Any]:
    """
    Return a dictionary with default configuration values.
    
    Returns:
        Dictionary containing default Paths, Seeds, ModelParams, and Thresholds.
    """
    paths = Paths()
    seeds = Seeds()
    model_params = ModelParams()
    thresholds = Thresholds()
    
    return {
        "paths": {
            "project_root": str(paths.project_root),
            "data_raw": str(paths.data_raw_dir),
            "data_processed": str(paths.data_processed_dir),
            "data_models": str(paths.data_models_dir),
            "data_reports": str(paths.data_reports_dir),
            "logs": str(paths.logs_dir),
            "contracts": str(paths.contracts_dir),
        },
        "seeds": seeds.get_all_seeds(),
        "model_params": {
            "cv_folds": model_params.cv_folds,
            "vif_threshold": model_params.vif_threshold,
            "l1_penalty_strength": model_params.l1_penalty_strength,
            "solver": model_params.solver,
            "max_iter": model_params.max_iter,
            "n_permutations": model_params.n_permutations,
            "shap_sample_size": model_params.shap_sample_size,
        },
        "thresholds": {
            "min_interactions_per_pathogen": thresholds.min_interactions_per_pathogen,
            "max_missing_data_ratio": thresholds.max_missing_data_ratio,
            "significance_level": thresholds.significance_level,
            "fdr_method": thresholds.fdr_method,
            "host_range_breadth_threshold": thresholds.host_range_breadth_threshold,
            "zero_interaction_halt": thresholds.zero_interaction_halt,
        },
    }