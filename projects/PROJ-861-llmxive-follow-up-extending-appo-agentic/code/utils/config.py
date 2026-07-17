import os
import random
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import numpy as np

class Config:
    """Configuration manager for the project."""
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """Initialize configuration with optional dictionary."""
        self.config = config_dict or {}
        self._set_defaults()
    
    def _set_defaults(self):
        """Set default configuration values."""
        defaults = {
            "random_seed": 42,
            "task_timeout_seconds": 300,  # 5 minutes per task
            "max_exclusion_rate": 0.20,   # 20% of tasks can be excluded
            "input_path": "data/processed/sampled_tasks.json",
            "output_path": "data/processed/static_scores.json",
            "model_path": "microsoft/phi-2",
            "device": "cpu",
            "batch_size": 32,
            "num_workers": 4,
            "log_level": "INFO",
            "log_file": "logs/batch_processor.log"
        }
        
        # Update with provided config
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
        
        # Override with environment variables if present
        self._load_env_overrides()
    
    def _load_env_overrides(self):
        """Load configuration overrides from environment variables."""
        env_mapping = {
            "RANDOM_SEED": "random_seed",
            "TASK_TIMEOUT_SECONDS": "task_timeout_seconds",
            "MAX_EXCLUSION_RATE": "max_exclusion_rate",
            "INPUT_PATH": "input_path",
            "OUTPUT_PATH": "output_path",
            "MODEL_PATH": "model_path",
            "DEVICE": "device",
            "BATCH_SIZE": "batch_size",
            "NUM_WORKERS": "num_workers",
            "LOG_LEVEL": "log_level",
            "LOG_FILE": "log_file"
        }
        
        for env_var, config_key in env_mapping.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Try to convert to appropriate type
                if config_key in ["random_seed", "task_timeout_seconds", "batch_size", "num_workers"]:
                    try:
                        self.config[config_key] = int(env_value)
                    except ValueError:
                        pass
                elif config_key in ["max_exclusion_rate"]:
                    try:
                        self.config[config_key] = float(env_value)
                    except ValueError:
                        pass
                else:
                    self.config[config_key] = env_value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self.config[key] = value
    
    def get_random_seed(self) -> int:
        """Get random seed and set it for reproducibility."""
        seed = self.config["random_seed"]
        random.seed(seed)
        np.random.seed(seed)
        return seed

def get_config(config_dict: Optional[Dict[str, Any]] = None) -> Config:
    """Get or create a configuration instance."""
    return Config(config_dict)

def main():
    """Main entry point for configuration testing."""
    config = get_config()
    
    # Print configuration
    print("Current Configuration:")
    for key, value in config.config.items():
        print(f"  {key}: {value}")
    
    # Test environment variable override
    os.environ["TASK_TIMEOUT_SECONDS"] = "600"
    config = get_config()
    print(f"\nAfter env override - task_timeout_seconds: {config.get('task_timeout_seconds')}")

if __name__ == "__main__":
    main()
