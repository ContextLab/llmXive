"""
Configuration management for the Brain Network Dynamics pipeline.

Handles environment variables, default paths, and random seeds for reproducibility.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import random
import numpy as np
from typing import Optional

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """
    Central configuration object for the pipeline.
    
    Attributes:
        project_root: Path to the project root directory.
        openneuro_id: The OpenNeuro dataset ID (e.g., 'ds000000').
        n_subjects: Number of subjects to process (subset for CI).
        stage: Current pipeline stage being executed.
        random_seed: Seed for reproducibility.
        data_raw: Path to raw data directory.
        data_processed: Path to processed data directory.
        data_metrics: Path to metrics output directory.
        reports_dir: Path to reports directory.
    """
    
    def __init__(
        self,
        openneuro_id: Optional[str] = None,
        n_subjects: int = 10,
        stage: str = "all",
        random_seed: int = 42,
    ):
        self.project_root = Path(__file__).resolve().parent.parent
        
        # Load OpenNeuro ID from argument or environment
        self.openneuro_id = openneuro_id or os.getenv("OPENNEURO_ID")
        self.n_subjects = n_subjects
        self.stage = stage
        self.random_seed = random_seed
        
        # Set seeds for reproducibility
        random.seed(self.random_seed)
        np.random.seed(self.random_seed)
        
        # Define directory paths
        self.data_raw = self.project_root / "data" / "raw"
        self.data_processed = self.project_root / "data" / "processed"
        self.data_metrics = self.project_root / "data" / "metrics"
        self.reports_dir = self.project_root / "reports"
        self.figures_dir = self.project_root / "figures"
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create necessary directory structure if it doesn't exist."""
        dirs = [
            self.data_raw,
            self.data_processed,
            self.data_metrics,
            self.reports_dir,
            self.figures_dir,
            self.project_root / "logs",
            self.project_root / "code" / "data",
            self.project_root / "code" / "analysis",
            self.project_root / "tests" / "unit",
            self.project_root / "tests" / "integration",
            self.project_root / "docs",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
    
    def __repr__(self):
        return (
            f"Config(openneuro_id={self.openneuro_id}, "
            f"n_subjects={self.n_subjects}, "
            f"stage={self.stage}, "
            f"seed={self.random_seed})"
        )