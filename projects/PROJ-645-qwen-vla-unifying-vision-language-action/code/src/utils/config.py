"""
Environment configuration management for the Qwen-VLA Cross-Embodiment Transfer Study.

Handles .env loading, default path resolution, and runtime configuration access.
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file if it exists in the project root
# Project root is assumed to be two levels up from this file (code/src/utils -> code -> root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_ENV_FILE_PATH = _PROJECT_ROOT / ".env"

if _ENV_FILE_PATH.exists():
    load_dotenv(_ENV_FILE_PATH)
else:
    # Attempt to load from current working directory if .env not in project root
    load_dotenv()

class Config:
    """
    Centralized configuration manager.
    
    Provides access to environment variables with fallback defaults for
    paths and hyperparameters required by the pipeline.
    """
    
    # --- Path Configuration ---
    _DEFAULT_DATA_DIR = _PROJECT_ROOT / "data"
    _DEFAULT_CODE_DIR = _PROJECT_ROOT / "code"
    _DEFAULT_LOGS_DIR = _PROJECT_ROOT / "logs"
    _DEFAULT_CHECKPOINTS_DIR = _DEFAULT_DATA_DIR / "checkpoints"
    _DEFAULT_EVAL_RESULTS_DIR = _DEFAULT_DATA_DIR / "eval_results"
    _DEFAULT_MANIFEST_PATH = _PROJECT_ROOT / "manifest.yaml"
    
    @classmethod
    def get_data_dir(cls) -> Path:
        """Returns the base data directory."""
        return Path(os.getenv("DATA_DIR", str(cls._DEFAULT_DATA_DIR)))

    @classmethod
    def get_code_dir(cls) -> Path:
        """Returns the base code directory."""
        return Path(os.getenv("CODE_DIR", str(cls._DEFAULT_CODE_DIR)))

    @classmethod
    def get_logs_dir(cls) -> Path:
        """Returns the base logs directory."""
        logs_dir = Path(os.getenv("LOGS_DIR", str(cls._DEFAULT_LOGS_DIR)))
        logs_dir.mkdir(parents=True, exist_ok=True)
        return logs_dir

    @classmethod
    def get_checkpoints_dir(cls) -> Path:
        """Returns the checkpoints directory, creating it if necessary."""
        checkpoints_dir = Path(os.getenv("CHECKPOINTS_DIR", str(cls._DEFAULT_CHECKPOINTS_DIR)))
        checkpoints_dir.mkdir(parents=True, exist_ok=True)
        return checkpoints_dir

    @classmethod
    def get_eval_results_dir(cls) -> Path:
        """Returns the evaluation results directory, creating it if necessary."""
        eval_dir = Path(os.getenv("EVAL_RESULTS_DIR", str(cls._DEFAULT_EVAL_RESULTS_DIR)))
        eval_dir.mkdir(parents=True, exist_ok=True)
        return eval_dir

    @classmethod
    def get_manifest_path(cls) -> Path:
        """Returns the path to the reproducibility manifest."""
        return Path(os.getenv("MANIFEST_PATH", str(cls._DEFAULT_MANIFEST_PATH)))

    @classmethod
    def get_dataset_path(cls, dataset_name: str) -> Path:
        """Constructs the full path for a specific dataset file."""
        return cls.get_data_dir() / f"{dataset_name}.parquet"

    # --- Hyperparameter & Runtime Configuration ---
    @classmethod
    def get_batch_size(cls) -> int:
        """Returns the training batch size (default 8)."""
        return int(os.getenv("BATCH_SIZE", "8"))

    @classmethod
    def get_num_epochs(cls) -> int:
        """Returns the number of training epochs (default 5)."""
        return int(os.getenv("NUM_EPOCHS", "5"))

    @classmethod
    def get_wall_time_limit_seconds(cls) -> int:
        """Returns the wall-time limit in seconds (default 21600 = 6 hours)."""
        return int(os.getenv("WALL_TIME_LIMIT_SECONDS", "21600"))

    @classmethod
    def get_ram_limit_gb(cls) -> float:
        """Returns the RAM limit in GB (default 7.0)."""
        return float(os.getenv("RAM_LIMIT_GB", "7.0"))

    @classmethod
    def get_num_threads(cls) -> int:
        """Returns the number of CPU threads for torch (default 2)."""
        return int(os.getenv("NUM_THREADS", "2"))

    @classmethod
    def get_model_name(cls) -> str:
        """Returns the base model name (default Qwen2-VL-2B)."""
        return os.getenv("MODEL_NAME", "Qwen2-VL-2B")

    @classmethod
    def get_experiment_seed(cls) -> int:
        """Returns the random seed for reproducibility."""
        return int(os.getenv("EXPERIMENT_SEED", "42"))

    @classmethod
    def get_experiment_name(cls) -> str:
        """Returns the experiment name for logging."""
        return os.getenv("EXPERIMENT_NAME", "qwen-vla-transfer")

    @classmethod
    def get_log_level(cls) -> int:
        """Returns the logging level (default INFO)."""
        level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        return getattr(logging, level_str, logging.INFO)

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Exports current configuration as a dictionary."""
        return {
            "paths": {
                "data_dir": str(cls.get_data_dir()),
                "code_dir": str(cls.get_code_dir()),
                "logs_dir": str(cls.get_logs_dir()),
                "checkpoints_dir": str(cls.get_checkpoints_dir()),
                "eval_results_dir": str(cls.get_eval_results_dir()),
                "manifest_path": str(cls.get_manifest_path()),
            },
            "hyperparameters": {
                "batch_size": cls.get_batch_size(),
                "num_epochs": cls.get_num_epochs(),
                "wall_time_limit_seconds": cls.get_wall_time_limit_seconds(),
                "ram_limit_gb": cls.get_ram_limit_gb(),
                "num_threads": cls.get_num_threads(),
                "experiment_seed": cls.get_experiment_seed(),
            },
            "runtime": {
                "model_name": cls.get_model_name(),
                "experiment_name": cls.get_experiment_name(),
                "log_level": cls.get_log_level(),
            }
        }

def main():
    """CLI entry point to dump current configuration."""
    import sys
    print(json.dumps(Config.to_dict(), indent=2))
    sys.exit(0)

if __name__ == "__main__":
    main()
