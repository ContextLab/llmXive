import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
from logging_config import get_logger

logger = get_logger(__name__)

class Config:
    """
    Global configuration management.
    Loads paths and settings from environment or defaults.
    """
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.code_dir = self.root_dir / "code"
        self.data_dir = self.root_dir / "data"
        self.models_dir = self.root_dir / "models"
        self.docs_dir = self.root_dir / "docs"
        self.figures_dir = self.root_dir / "figures"
        
        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        
        # Random seed
        self.random_seed = int(os.getenv("RANDOM_SEED", "42"))
        
        # API Keys (loaded from env)
        self.mp_api_key = os.getenv("MP_API_KEY")
        
        logger.info(f"Config initialized. Root: {self.root_dir}")

_config_instance: Optional[Config] = None

def get_config() -> Config:
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def main():
    cfg = get_config()
    print(f"Data Dir: {cfg.data_dir}")
    print(f"Models Dir: {cfg.models_dir}")

if __name__ == "__main__":
    main()
