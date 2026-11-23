"""Configuration management for staleness, seeds, and model settings."""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

class Config:
    """Central configuration loader and validator."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.base_dir = Path(__file__).parent.parent.parent
        self.config_path = config_path or os.getenv("LLMXIVE_CONFIG", "config.json")
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file or environment."""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                self._config = json.load(f)
        else:
            # Default configuration
            self._config = {
                "staleness": {
                    "low": 1,
                    "high": 5,
                    "adaptive": True
                },
                "seeds": list(range(1, 6)),
                "models": ["phi-2", "qwen1.5-1.8b"],
                "max_memory_gb": 6.5
            }
        
        # Check for verified source override
        if "VERIFIED_REAL_DATA_SOURCE" in os.environ:
            self._config["data_source"] = os.environ["VERIFIED_REAL_DATA_SOURCE"]
        else:
            self._config["data_source"] = "openai/gsm8k"
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation key."""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def get_staleness_config(self) -> Dict[str, Any]:
        """Get staleness configuration."""
        return self._config.get("staleness", {})
    
    def get_seed_sequence(self) -> list:
        """Get the sequence of seeds to use."""
        return self._config.get("seeds", list(range(1, 6)))
    
    def get_model_ids(self) -> list:
        """Get list of model IDs to train."""
        return self._config.get("models", ["phi-2", "qwen1.5-1.8b"])
    
    def get_max_memory_gb(self) -> float:
        """Get maximum allowed memory in GB."""
        return float(self._config.get("max_memory_gb", 6.5))
    
    def get_data_source(self) -> str:
        """Get the data source (dataset name or URL)."""
        return self._config.get("data_source", "openai/gsm8k")
