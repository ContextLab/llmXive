"""
Environment configuration management for the llmXive research pipeline.

This module handles loading and validating configuration from environment variables
with sensible defaults for the data cleaning impact study.
"""
import os
from typing import List, Optional
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

# Configuration keys and defaults
CONFIG_KEYS = {
    "DATASET_URLS": {
        "type": list,
        "default": [
            "https://archive.ics.uci.edu/ml/machine-learning-databases/00244/UCI-HAR-Dataset.zip",
            "https://archive.ics.uci.edu/ml/machine-learning-databases/00518/UCI-Shopper-Dataset.zip"
        ],
        "description": "Comma-separated list of dataset URLs to download"
    },
    "OUTPUT_PATH": {
        "type": str,
        "default": "data/processed",
        "description": "Directory path for processed data outputs"
    },
    "RANDOM_SEED": {
        "type": int,
        "default": 42,
        "description": "Random seed for reproducibility"
    },
    "BOOTSTRAP_ITERATIONS": {
        "type": int,
        "default": 1000,
        "description": "Number of bootstrap iterations for variance estimation"
    }
}

class Config:
    """
    Configuration container class for project settings.
    
    Attributes:
        dataset_urls (List[str]): List of URLs to download datasets from.
        output_path (str): Directory path for processed data outputs.
        random_seed (int): Random seed for reproducibility.
        bootstrap_iterations (int): Number of bootstrap iterations.
    """
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        self.dataset_urls: List[str] = []
        self.output_path: str = ""
        self.random_seed: int = 0
        self.bootstrap_iterations: int = 0
        
        self._load_from_env()
        self._validate()
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        # DATASET_URLS
        urls_env = os.getenv("DATASET_URLS")
        if urls_env:
            self.dataset_urls = [url.strip() for url in urls_env.split(",")]
        else:
            self.dataset_urls = CONFIG_KEYS["DATASET_URLS"]["default"]
        
        # OUTPUT_PATH
        self.output_path = os.getenv("OUTPUT_PATH", CONFIG_KEYS["OUTPUT_PATH"]["default"])
        
        # RANDOM_SEED
        try:
            seed_env = os.getenv("RANDOM_SEED")
            self.random_seed = int(seed_env) if seed_env else CONFIG_KEYS["RANDOM_SEED"]["default"]
        except ValueError:
            self.random_seed = CONFIG_KEYS["RANDOM_SEED"]["default"]
        
        # BOOTSTRAP_ITERATIONS
        try:
            boot_env = os.getenv("BOOTSTRAP_ITERATIONS")
            self.bootstrap_iterations = int(boot_env) if boot_env else CONFIG_KEYS["BOOTSTRAP_ITERATIONS"]["default"]
        except ValueError:
            self.bootstrap_iterations = CONFIG_KEYS["BOOTSTRAP_ITERATIONS"]["default"]
    
    def _validate(self):
        """Validate configuration values."""
        if not self.dataset_urls:
            raise ValueError("DATASET_URLS cannot be empty")
        
        if not self.output_path:
            raise ValueError("OUTPUT_PATH cannot be empty")
        
        if self.random_seed < 0:
            raise ValueError("RANDOM_SEED must be non-negative")
        
        if self.bootstrap_iterations < 100:
            raise ValueError("BOOTSTRAP_ITERATIONS must be at least 100")
    
    def __repr__(self) -> str:
        return (
            f"Config(dataset_urls={self.dataset_urls}, "
            f"output_path={self.output_path}, "
            f"random_seed={self.random_seed}, "
            f"bootstrap_iterations={self.bootstrap_iterations})"
        )

# Singleton instance
_config_instance: Optional[Config] = None

def get_config() -> Config:
    """
    Get the singleton configuration instance.
    
    Returns:
        Config: The global configuration instance.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def reload_config() -> Config:
    """
    Force reload of the configuration from environment variables.
    
    Returns:
        Config: The refreshed configuration instance.
    """
    global _config_instance
    _config_instance = Config()
    return _config_instance