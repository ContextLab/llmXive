"""
Configuration management for the llmXive follow-up pipeline.
Handles seeds, paths, and timeout limits.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

# Base project root (assumed to be the directory containing this file's parent)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = PROJECT_ROOT / "projects" / "PROJ-915-llmxive-follow-up-extending-measuring-ep"

# Default paths relative to PROJECT_ROOT
DEFAULT_CONFIG = {
    "paths": {
        "data_raw": str(PROJECT_ROOT / "data" / "raw"),
        "data_processed": str(PROJECT_ROOT / "data" / "processed"),
        "data_interim": str(PROJECT_ROOT / "data" / "interim"),
        "data_results": str(PROJECT_ROOT / "data" / "results"),
        "code": str(PROJECT_ROOT / "code"),
        "tests": str(PROJECT_ROOT / "tests"),
        "specs": str(PROJECT_ROOT / "specs"),
        "state": str(PROJECT_ROOT / "state"),
    },
    "seeds": {
        "random_seed": 42,
        "nltk_seed": 42,
    },
    "limits": {
        "inference_timeout_seconds": 30,
        "pipeline_timeout_seconds": 3600,
        "max_retries": 3,
    },
    "models": {
        "llm_path": "TinyLlama-1.1B-Chat",
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    },
    "datasets": {
        "medmis_bench_name": "medmis-bench", # Placeholder, actual name from datasets lib
        "subset_labels": ["Authority-framed", "Exception-poisoning"],
    }
}

class Config:
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or (PROJECT_ROOT / "config.yaml")
        self._config = DEFAULT_CONFIG.copy()
        self._load_config()
        self._load_env()

    def _load_config(self):
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    self._deep_update(self._config, user_config)

    def _load_env(self):
        # Load from .env if available
        env_path = PROJECT_ROOT / ".env"
        if env_path.exists():
            from dotenv import load_dotenv
            load_dotenv(env_path)
        
        # Override specific values from environment
        if os.getenv("PIPELINE_TIMEOUT_LIMIT"):
            self._config["limits"]["pipeline_timeout_seconds"] = int(os.getenv("PIPELINE_TIMEOUT_LIMIT"))
        if os.getenv("RANDOM_SEED"):
            self._config["seeds"]["random_seed"] = int(os.getenv("RANDOM_SEED"))

    def _deep_update(self, base: Dict, override: Dict):
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get value by dot-notation path, e.g., 'paths.data_raw'"""
        keys = key_path.split(".")
        current = self._config
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        return current

    @property
    def paths(self) -> Dict[str, str]:
        return self._config["paths"]

    @property
    def seeds(self) -> Dict[str, int]:
        return self._config["seeds"]

    @property
    def limits(self) -> Dict[str, int]:
        return self._config["limits"]

    @property
    def models(self) -> Dict[str, str]:
        return self._config["models"]

    @property
    def datasets(self) -> Dict[str, Any]:
        return self._config["datasets"]

# Global instance
config = Config()

if __name__ == "__main__":
    import json
    print(json.dumps(config._config, indent=2, default=str))
