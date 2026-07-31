import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
from logging_config import get_logger

logger = get_logger(__name__)

class Config:
    """Configuration manager for the project."""
    
    def __init__(self):
        # Project root
        self.project_root = Path(__file__).parent.parent
        
        # Directory paths
        self.data_raw_dir = self.project_root / "data" / "raw"
        self.data_processed_dir = self.project_root / "data" / "processed"
        self.models_dir = self.project_root / "models"
        self.results_dir = self.project_root / "results"
        self.figures_dir = self.project_root / "figures"
        self.logs_dir = self.project_root / "data" / "logs"
        
        # Create directories if they don't exist
        for dir_path in [self.data_raw_dir, self.data_processed_dir, self.models_dir, 
                        self.results_dir, self.figures_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Random seed
        self.random_seed = 42
        
        # API keys and tokens
        self.materials_project_api_key = os.getenv("MP_API_KEY", "")
        self.nist_api_key = os.getenv("NIST_API_KEY", "")
        
        logger.info("Configuration initialized")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "project_root": str(self.project_root),
            "data_raw_dir": str(self.data_raw_dir),
            "data_processed_dir": str(self.data_processed_dir),
            "models_dir": str(self.models_dir),
            "results_dir": str(self.results_dir),
            "figures_dir": str(self.figures_dir),
            "logs_dir": str(self.logs_dir),
            "random_seed": self.random_seed
        }

def get_config() -> Config:
    """Get or create configuration instance."""
    if not hasattr(get_config, '_instance'):
        get_config._instance = Config()
    return get_config._instance

def main():
    """Main entry point for configuration."""
    config = get_config()
    print(json.dumps(config.to_dict(), indent=2))

if __name__ == "__main__":
    main()
