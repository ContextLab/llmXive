"""
Configuration management for the gene expression dimensionality study.
Defines paths, seeds, and dataset accessions.
"""
import os
from pathlib import Path
import logging
import random
import numpy as np

# Base project directory (assumed to be the root where this script is run)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

class Config:
    def __init__(self):
        # Directories
        self.data_dir = PROJECT_ROOT / "data"
        self.data_raw = self.data_dir / "raw"
        self.data_processed = self.data_dir / "processed"
        self.results_dir = PROJECT_ROOT / "results"
        self.figures_dir = self.results_dir / "figures"
        
        # Create directories if they don't exist
        self.data_raw.mkdir(parents=True, exist_ok=True)
        self.data_processed.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.figures_dir.mkdir(parents=True, exist_ok=True)

        # Logging
        self.log_file = self.results_dir / "pipeline.log"

        # Random Seeds
        self.random_seed = 42
        self._set_global_seeds()

        # Dataset Accessions
        self.accessions = ["GSE131907", "GSE111322", "GSE150728"]

        # Analysis Parameters
        self.hvg_top_n = 2000
        self.sampling_threshold = 10000  # Max cells before sampling
        self.n_pcs = 50
        self.leiden_resolutions = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

        # Resource Limits
        self.max_ram_gb = 7.0
        self.max_runtime_hours = 6.0

    def _set_global_seeds(self):
        """Set global random seeds for reproducibility."""
        random.seed(self.random_seed)
        np.random.seed(self.random_seed)
        # If TensorFlow or PyTorch were used, we would set seeds there too.
        # os.environ['PYTHONHASHSEED'] = str(self.random_seed)

# Global instance
CONFIG = Config()

# Setup basic logging format for the module
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )