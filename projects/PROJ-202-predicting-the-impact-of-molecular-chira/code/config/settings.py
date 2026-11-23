"""
Environment configuration management for the molecular chirality pipeline.

This module handles loading environment variables, setting default paths,
and providing a centralized configuration object.
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Project root directory (parent of the 'code' directory)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Default directory paths
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_DATA_RAW = DEFAULT_DATA_DIR / "raw"
DEFAULT_DATA_PROCESSED = DEFAULT_DATA_DIR / "processed"
DEFAULT_DATA_INTERIM = DEFAULT_DATA_DIR / "interim"
DEFAULT_LOGS_DIR = DEFAULT_DATA_DIR / "logs"
DEFAULT_FIGURES_DIR = DEFAULT_DATA_DIR / "figures"
DEFAULT_RESULTS_DIR = DEFAULT_DATA_DIR / "results"

# Default file paths
DEFAULT_LOG_FILE = DEFAULT_LOGS_DIR / "pipeline.log"
DEFAULT_SEED = 42

# API Keys and Secrets (loaded from environment, with safe defaults)
# Note: FlavorDB and ChEMBL do not require API keys for basic access,
# but we provide placeholders for future extensibility.
CHEMBL_API_KEY: Optional[str] = os.getenv("CHEMBL_API_KEY")
FLAVORDB_API_KEY: Optional[str] = os.getenv("FLAVORDB_API_KEY")
ALPHA_FOLD_DB_URL: str = os.getenv(
    "ALPHA_FOLD_DB_URL",
    "https://alphafold.ebi.ac.uk/api/prediction/"
)

# Computational parameters
MAX_RAM_GB: int = int(os.getenv("MAX_RAM_GB", "7"))
CPU_CORES: int = int(os.getenv("CPU_CORES", "2"))
DOCKING_TIMEOUT_MINUTES: int = int(os.getenv("DOCKING_TIMEOUT_MINUTES", "10"))
MD_STEPS: int = int(os.getenv("MD_STEPS", "100000"))  # 100ps at 1fs step
MD_TEMP_K: float = float(os.getenv("MD_TEMP_K", "300.0"))

# Sensitivity analysis thresholds (FR-007)
SENSITIVITY_THRESHOLDS = [0.4, 0.5, 0.6]

# Dataset limits (reduced for CPU feasibility)
MAX_ENANTIOMER_PAIRS: int = int(os.getenv("MAX_ENANTIOMER_PAIRS", "10"))
MAX_RECEPTORS: int = int(os.getenv("MAX_RECEPTORS", "3"))

class Config:
    """Centralized configuration object."""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.data_dir = DEFAULT_DATA_DIR
        self.data_raw = DEFAULT_DATA_RAW
        self.data_processed = DEFAULT_DATA_PROCESSED
        self.data_interim = DEFAULT_DATA_INTERIM
        self.logs_dir = DEFAULT_LOGS_DIR
        self.figures_dir = DEFAULT_FIGURES_DIR
        self.results_dir = DEFAULT_RESULTS_DIR
        self.log_file = DEFAULT_LOG_FILE
        self.seed = int(os.getenv("RANDOM_SEED", DEFAULT_SEED))
        
        # API Keys
        self.chembl_api_key = CHEMBL_API_KEY
        self.flavordb_api_key = FLAVORDB_API_KEY
        self.alpha_fold_db_url = ALPHA_FOLD_DB_URL
        
        # Compute constraints
        self.max_ram_gb = MAX_RAM_GB
        self.cpu_cores = CPU_CORES
        self.docking_timeout_minutes = DOCKING_TIMEOUT_MINUTES
        
        # MD parameters
        self.md_steps = MD_STEPS
        self.md_temp_k = MD_TEMP_K
        
        # Analysis parameters
        self.sensitivity_thresholds = SENSITIVITY_THRESHOLDS
        self.max_enantiomer_pairs = MAX_ENANTIOMER_PAIRS
        self.max_receptors = MAX_RECEPTORS

    def ensure_directories(self):
        """Create all necessary directories if they don't exist."""
        dirs = [
            self.data_raw,
            self.data_processed,
            self.data_interim,
            self.logs_dir,
            self.figures_dir,
            self.results_dir
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
        return dirs

    def get_chembl_url(self, target: str = "molecule") -> str:
        """Construct ChEMBL API URL."""
        base = "https://www.ebi.ac.uk/chembl/api/data"
        return f"{base}/{target}.json"

    def get_alpha_fold_url(self, protein_id: str) -> str:
        """Construct AlphaFold DB URL for a specific protein."""
        return f"{self.alpha_fold_db_url}/{protein_id}"

# Global configuration instance
config = Config()
