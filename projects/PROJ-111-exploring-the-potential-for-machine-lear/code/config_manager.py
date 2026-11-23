import os
import logging
from pathlib import Path
from typing import Optional, List, Any
from dotenv import load_dotenv

# Ensure .env is loaded from project root
load_dotenv()

logger = logging.getLogger("llmXive.config")

class Config:
    """
    Centralized configuration management using environment variables.
    Loads values from .env file with fallbacks to defaults.
    """
    
    def __init__(self):
        # Random Seeds
        self.random_seed = int(os.getenv("RANDOM_SEED", "42"))
        self.torch_seed = int(os.getenv("TORCH_SEED", "42"))
        self.numpy_seed = int(os.getenv("NUMPY_SEED", "42"))
        
        # Paths
        self.project_root = Path(os.getenv("PROJECT_ROOT", "."))
        self.data_raw_dir = self.project_root / os.getenv("DATA_RAW_DIR", "data/raw")
        self.data_processed_dir = self.project_root / os.getenv("DATA_PROCESSED_DIR", "data/processed")
        self.figures_dir = self.project_root / os.getenv("FIGURES_DIR", "figures")
        self.logs_dir = self.project_root / os.getenv("LOGS_DIR", "logs")
        self.checkpoint_dir = self.project_root / os.getenv("CHECKPOINT_DIR", "code/checkpoints")
        
        # Simulation Parameters
        self.lattice_sizes = [int(x) for x in os.getenv("LATTICE_SIZES", "16,24").split(",")]
        self.temp_min = float(os.getenv("TEMPERATURE_RANGE_MIN", "0.1"))
        self.temp_max = float(os.getenv("TEMPERATURE_RANGE_MAX", "3.0"))
        self.temp_step = float(os.getenv("TEMPERATURE_STEP", "0.1"))
        self.coupling_j1 = float(os.getenv("COUPLING_J1", "1.0"))
        self.coupling_j2_ratio = float(os.getenv("COUPLING_J2_RATIO", "0.5"))
        
        # Training Parameters
        self.batch_size = int(os.getenv("BATCH_SIZE", "32"))
        self.learning_rate = float(os.getenv("LEARNING_RATE", "0.001"))
        self.epochs = int(os.getenv("EPOCHS", "100"))
        self.early_stopping_patience = int(os.getenv("EARLY_STOPPING_PATIENCE", "5"))
        self.max_memory_gb = float(os.getenv("MAX_MEMORY_GB", "6.0"))
        
        # Logging
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_format = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self.log_file = os.getenv("LOG_FILE", "logs/project.log")
        
        # Validate paths exist or create them
        self._ensure_directories()

    def _ensure_directories(self):
        """Creates necessary directories if they don't exist."""
        dirs = [
            self.data_raw_dir,
            self.data_processed_dir,
            self.figures_dir,
            self.logs_dir,
            self.checkpoint_dir
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {d}")

    def get_paths(self) -> dict:
        """Returns a dictionary of all path configurations."""
        return {
            "project_root": str(self.project_root),
            "data_raw": str(self.data_raw_dir),
            "data_processed": str(self.data_processed_dir),
            "figures": str(self.figures_dir),
            "logs": str(self.logs_dir),
            "checkpoints": str(self.checkpoint_dir)
        }

    def get_simulation_params(self) -> dict:
        """Returns simulation parameters."""
        return {
            "lattice_sizes": self.lattice_sizes,
            "temp_range": (self.temp_min, self.temp_max),
            "temp_step": self.temp_step,
            "coupling_j1": self.coupling_j1,
            "coupling_j2_ratio": self.coupling_j2_ratio
        }

    def get_training_params(self) -> dict:
        """Returns training parameters."""
        return {
            "batch_size": self.batch_size,
            "learning_rate": self.learning_rate,
            "epochs": self.epochs,
            "early_stopping_patience": self.early_stopping_patience,
            "max_memory_gb": self.max_memory_gb
        }

# Singleton instance
_config_instance: Optional[Config] = None

def get_config() -> Config:
    """Returns the singleton Config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def reset_config() -> None:
    """Resets the singleton instance (useful for testing)."""
    global _config_instance
    _config_instance = None
