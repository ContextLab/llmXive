"""
Configuration module for the Algorithmic Recommendations Analysis Pipeline.

This module defines all project-wide constants, paths, random seeds, and
hyperparameters required for reproducibility and consistent execution.

It provides a centralized `ProjectConfig` class to manage these settings,
ensuring that paths are resolved relative to the project root and that
seeds are set for deterministic behavior in metrics and modeling.
"""
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import logging

# Set up logger for config diagnostics
logger = logging.getLogger(__name__)

@dataclass
class ProjectConfig:
    """
    Central configuration container for the research pipeline.
    
    Attributes:
        project_root: The absolute path to the project root directory.
        data_root: Path to the data directory.
        processed_data_path: Path to the processed data directory.
        output_dir: Path for final outputs (reports, figures).
        seed: Random seed for reproducibility (numpy, pandas, python).
        similarity_threshold: Semantic similarity threshold for category merging.
        min_enrollments: Minimum number of enrollments required for a valid session.
        psw_max_weight: Maximum allowed stabilized weight for PSW (outlier check).
        psw_min_n: Minimum sample size to attempt PSW before GLS fallback.
        permutation_iterations: Number of iterations for residual permutation test.
        sensitivity_thresholds: List of similarity thresholds for sensitivity analysis.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR).
    """
    # Paths
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    data_root: Path = field(init=False)
    processed_data_path: Path = field(init=False)
    output_dir: Path = field(init=False)
    figures_dir: Path = field(init=False)
    reports_dir: Path = field(init=False)
    
    # Reproducibility
    seed: int = 42
    
    # Hyperparameters & Thresholds
    similarity_threshold: float = 0.1
    min_enrollments: int = 1
    psw_max_weight: float = 10.0
    psw_min_n: int = 30
    permutation_iterations: int = 1000
    sensitivity_thresholds: List[float] = field(default_factory=lambda: [0.01, 0.05, 0.1])
    
    # Logging
    log_level: str = "INFO"

    def __post_init__(self):
        """Initialize derived paths based on project_root."""
        self.data_root = self.project_root / "data"
        self.processed_data_path = self.data_root / "processed"
        self.output_dir = self.project_root / "output"
        self.figures_dir = self.output_dir / "figures"
        self.reports_dir = self.output_dir / "reports"
        
        # Ensure directories exist
        self._ensure_dirs()
        
        # Set global random seeds
        self._set_seeds()

    def _ensure_dirs(self):
        """Create necessary directories if they do not exist."""
        dirs = [
            self.data_root,
            self.processed_data_path,
            self.output_dir,
            self.figures_dir,
            self.reports_dir
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directories exist: {dirs}")

    def _set_seeds(self):
        """Set random seeds for reproducibility."""
        import random
        import numpy as np
        
        try:
            import torch
            torch.manual_seed(self.seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(self.seed)
        except ImportError:
            pass
        
        random.seed(self.seed)
        np.random.seed(self.seed)
        
        logger.info(f"Random seeds set to {self.seed} for reproducibility.")

# Global instance for easy access
config = ProjectConfig()

# Convenience constants for file paths
RAW_DATA_PATH = config.data_root / "raw"
PROCESSED_DATA_PATH = config.processed_data_path
FINAL_REPORT_PATH = config.reports_dir / "final_analysis.md"
SUMMARY_JSON_PATH = config.output_dir / "summary.json"

# Pipeline Constants
REQUIRED_COLUMNS = ["recommended_categories", "enrolled_categories", "user_id", "session_id"]
PSW_WEIGHT_COLUMN = "stabilized_weight"
BASELINE_VECTOR_COLUMN = "baseline_interest_vector"

# Logging Configuration
def setup_logging():
    """Configure logging based on config.log_level."""
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger.info(f"Logging configured at level {config.log_level}")

# Initialize logging on import
setup_logging()

# Export public API
__all__ = [
    "ProjectConfig",
    "config",
    "RAW_DATA_PATH",
    "PROCESSED_DATA_PATH",
    "FINAL_REPORT_PATH",
    "SUMMARY_JSON_PATH",
    "REQUIRED_COLUMNS",
    "PSW_WEIGHT_COLUMN",
    "BASELINE_VECTOR_COLUMN",
    "setup_logging"
]