import os
import random
import numpy as np
from pathlib import Path
from typing import Dict, List, Set, Optional, Any

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data Paths
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_ANALYSIS_DIR = PROJECT_ROOT / "data" / "analysis"
MODELS_DIR = PROJECT_ROOT / "models"
ANALYSIS_DIR = PROJECT_ROOT / "analysis"
TESTS_DIR = PROJECT_ROOT / "tests"
DOCS_DIR = PROJECT_ROOT / "docs"

# City Mapping Constants (Target Chinese Cities for T006 filtering)
# These match the filter criteria in data/preprocess.py
TARGET_CITIES: Set[str] = {
    "Beijing",
    "Shanghai",
    "Guangzhou",
    "Shenzhen"
}

# Route Length Categories (Stratification thresholds)
# Short: < 15 stops
# Medium: 15 - 30 stops
# Long: > 30 stops
SHORT_ROUTE_THRESHOLD: int = 15
MEDIUM_ROUTE_THRESHOLD: int = 30

# Model Hyperparameters
TOP_N_NEIGHBORS: int = 5
VOCAB_TOP_K: int = 5000
UNKNOWN_TOKEN: str = "<UNKNOWN>"

# Statistical Analysis Thresholds
VALIDITY_DROP_THRESHOLD: float = 0.15  # 15% drop
CHI_SQUARED_P_VALUE_THRESHOLD: float = 0.05

# Resource Constraints (Simulation)
MAX_MEMORY_MB: int = 4096  # 4GB
MAX_INFERENCE_TIME_SECONDS: float = 60.0

class Config:
    """
    Central configuration class for environment variables, seeds, and constants.
    """
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.set_seed(seed)
        
        # Environment overrides
        self.debug_mode = os.getenv("LLMXIVE_DEBUG", "false").lower() == "true"
        self.cache_dir = os.getenv("HF_HOME", str(PROJECT_ROOT / ".cache" / "huggingface"))
        
        # Ensure directories exist
        self._ensure_directories()

    def set_seed(self, seed: int) -> None:
        """Set random seeds for reproducibility."""
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)
        # If torch is available, set its seed too (optional, guarded)
        try:
            import torch
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)
        except ImportError:
            pass

    def _ensure_directories(self) -> None:
        """Create project directories if they don't exist."""
        dirs = [
            DATA_RAW_DIR,
            DATA_PROCESSED_DIR,
            DATA_ANALYSIS_DIR,
            MODELS_DIR,
            ANALYSIS_DIR,
            TESTS_DIR,
            DOCS_DIR
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def get_city_filter(self) -> Set[str]:
        """Return the set of target cities for filtering."""
        return TARGET_CITIES.copy()

    def get_stratification_bounds(self) -> tuple:
        """Return the (short_max, medium_max) bounds for route length."""
        return (SHORT_ROUTE_THRESHOLD, MEDIUM_ROUTE_THRESHOLD)

def get_env_config() -> Dict[str, Any]:
    """
    Fetches configuration from environment variables with defaults.
    Useful for CI/CD or containerized runs.
    """
    return {
        "debug": os.getenv("LLMXIVE_DEBUG", "false").lower() == "true",
        "seed": int(os.getenv("LLMXIVE_SEED", "42")),
        "data_root": str(PROJECT_ROOT),
        "raw_data_path": str(DATA_RAW_DIR),
        "processed_data_path": str(DATA_PROCESSED_DIR),
        "analysis_output_path": str(DATA_ANALYSIS_DIR),
        "target_cities": list(TARGET_CITIES),
    }

def set_global_seed(seed: int) -> None:
    """Convenience function to set the global random seed."""
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

# Instantiate default config if imported directly
config = Config()