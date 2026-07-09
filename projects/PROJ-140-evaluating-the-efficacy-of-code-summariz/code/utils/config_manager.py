import os
import json
from pathlib import Path
from typing import Any, Dict, Optional, List
from dotenv import load_dotenv
import random
import numpy as np
import sys

# Attempt to load .env from the code directory or project root
_env_path = Path(__file__).parent / ".env"
if not _env_path.exists():
    _env_path = Path(__file__).parent.parent / ".env"

if _env_path.exists():
    load_dotenv(_env_path)

class Config:
    """
    Centralized configuration manager for the llmXive project.
    Loads settings from environment variables (.env file).
    """
    
    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._load_config()
        
        # Initialize global seeds based on config
        self._init_seeds()

    def _load_config(self) -> None:
        """Load configuration from environment variables."""
        self._config = {
            # Paths
            "project_root": os.getenv("PROJECT_ROOT", "."),
            "data_dir": os.getenv("DATA_DIR", "data"),
            "code_dir": os.getenv("CODE_DIR", "code"),
            "state_dir": os.getenv("STATE_DIR", "state"),
            
            # Subdirectories
            "defects4j_dir": os.getenv("DEFECTS4J_DIR", "data/defects4j"),
            "summaries_dir": os.getenv("SUMMARIES_DIR", "data/summaries"),
            "interaction_logs_dir": os.getenv("INTERACTION_LOGS_DIR", "data/interaction_logs"),
            "analysis_results_dir": os.getenv("ANALYSIS_RESULTS_DIR", "data/analysis_results"),
            "consent_dir": os.getenv("CONSENT_DIR", "data/consent"),
            
            # Seeds
            "random_seed": int(os.getenv("RANDOM_SEED", "42")),
            "np_seed": int(os.getenv("NP_SEED", "42")),
            "torch_seed": int(os.getenv("TORCH_SEED", "42")),
            
            # Constraints
            "max_runtime_seconds": int(os.getenv("MAX_RUNTIME_SECONDS", "21600")),
            "max_ram_gb": int(os.getenv("MAX_RAM_GB", "7")),
            
            # Analysis
            "sensitivity_cutoffs": [float(x) for x in os.getenv("SENSITIVITY_CUTOFFS", "0.01,0.05,0.10").split(",")],
            "bootstrap_resamples": int(os.getenv("BOOTSTRAP_RESAMPLES", "1000")),
            
            # LLM
            "real_llm_model_name": os.getenv("REAL_LLM_MODEL_NAME", "codellama/CodeLlama-7b-hf"),
            "real_llm_quantization": os.getenv("REAL_LLM_QUANTIZATION", "8bit"),
            
            # Logging
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "log_file": os.getenv("LOG_FILE", "state/logs/app.log"),
        }

    def _init_seeds(self) -> None:
        """Initialize random seeds for reproducibility."""
        seed = self._config["random_seed"]
        random.seed(seed)
        np.random.seed(seed)
        
        # Check if torch is available and set seed
        try:
            import torch
            torch.manual_seed(self._config["torch_seed"])
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(self._config["torch_seed"])
        except ImportError:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a configuration value by key."""
        return self._config.get(key, default)

    def get_path(self, key: str) -> Path:
        """Retrieve a configuration value as a Path object, resolved relative to project root."""
        path_str = self._config.get(key)
        if not path_str:
            raise KeyError(f"Configuration key '{key}' not found")
        
        base = Path(self._config["project_root"])
        return (base / path_str).resolve()

    def get_int(self, key: str) -> int:
        return int(self._config[key])

    def get_float(self, key: str) -> float:
        return float(self._config[key])

    def get_list(self, key: str) -> List[Any]:
        return self._config[key]

    def to_dict(self) -> Dict[str, Any]:
        """Return the full configuration as a dictionary."""
        return self._config.copy()


# Global singleton instance
_config_instance: Optional[Config] = None

def get_config() -> Config:
    """
    Returns the singleton Config instance.
    Ensures seeds are initialized on first call.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
