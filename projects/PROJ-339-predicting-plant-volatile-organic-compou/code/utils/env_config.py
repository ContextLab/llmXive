"""
Environment variable management for data paths and random seeds.

This module provides a centralized configuration manager that loads
environment variables from a .env file and provides typed accessors
for all project paths and seed values.

Usage:
    from utils.env_config import get_config
    
    config = get_config()
    data_path = config.data_root
    seed = config.random_seed
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
# This is called once at module import time
load_dotenv()

class EnvConfigError(Exception):
    """Custom exception for environment configuration errors."""
    pass

class EnvConfig:
    """
    Centralized environment variable management for data paths and seeds.
    
    Attributes:
        project_root (Path): Root directory of the project.
        data_root (Path): Root directory for all data.
        data_raw (Path): Directory for raw data.
        data_processed (Path): Directory for processed data.
        data_results (Path): Directory for results and reports.
        data_models (Path): Directory for model artifacts.
        specs_root (Path): Root directory for specifications.
        random_seed (int): Global random seed for reproducibility.
        n_jobs (int): Number of parallel jobs for processing.
        verbose (bool): Whether to print verbose output.
    """
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Project root (parent of code/ directory)
        self.project_root = Path(os.getenv('PROJECT_ROOT', str(Path(__file__).parent.parent.parent)))
        
        # Data directories
        self.data_root = Path(os.getenv('DATA_ROOT', self.project_root / 'data'))
        self.data_raw = Path(os.getenv('DATA_RAW', self.data_root / 'raw'))
        self.data_processed = Path(os.getenv('DATA_PROCESSED', self.data_root / 'processed'))
        self.data_results = Path(os.getenv('DATA_RESULTS', self.data_root / 'results'))
        self.data_models = Path(os.getenv('DATA_MODELS', self.data_root / 'models'))
        
        # Specifications directory
        self.specs_root = Path(os.getenv('_SPECS_ROOT', self.project_root / 'specs'))
        
        # Random seed for reproducibility
        self.random_seed = int(os.getenv('RANDOM_SEED', '42'))
        
        # Parallel processing settings
        self.n_jobs = int(os.getenv('N_JOBS', '-1'))
        self.verbose = os.getenv('VERBOSE', 'false').lower() == 'true'
        
        # Validation
        self._validate()
    
    def _validate(self):
        """Validate that all required directories exist."""
        required_dirs = [
            self.data_raw,
            self.data_processed,
            self.data_results,
            self.data_models,
            self.specs_root
        ]
        
        for directory in required_dirs:
            if not directory.exists():
                raise EnvConfigError(
                    f"Required directory does not exist: {directory}. "
                    f"Please ensure project setup (T001a) has been completed."
                )
    
    def get_path(self, key: str) -> Path:
        """
        Get a path by key name.
        
        Args:
            key: One of 'data_raw', 'data_processed', 'data_results', 'data_models', 'specs'
        
        Returns:
            Path object for the requested directory
        
        Raises:
            EnvConfigError: If the key is invalid
        """
        path_map = {
            'data_raw': self.data_raw,
            'data_processed': self.data_processed,
            'data_results': self.data_results,
            'data_models': self.data_models,
            'specs': self.specs_root,
            'data_root': self.data_root,
            'project_root': self.project_root
        }
        
        if key not in path_map:
            raise EnvConfigError(f"Unknown path key: {key}")
        
        return path_map[key]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        return {
            'project_root': str(self.project_root),
            'data_root': str(self.data_root),
            'data_raw': str(self.data_raw),
            'data_processed': str(self.data_processed),
            'data_results': str(self.data_results),
            'data_models': str(self.data_models),
            'specs_root': str(self.specs_root),
            'random_seed': self.random_seed,
            'n_jobs': self.n_jobs,
            'verbose': self.verbose
        }
    
    def save_to_json(self, path: Path) -> None:
        """
        Save configuration to a JSON file.
        
        Args:
            path: Path to save the configuration JSON
        """
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def from_json(cls, path: Path) -> 'EnvConfig':
        """
        Load configuration from a JSON file.
        
        Args:
            path: Path to the configuration JSON file
        
        Returns:
            EnvConfig instance
        """
        with open(path, 'r') as f:
            config_data = json.load(f)
        
        # Set environment variables from config
        for key, value in config_data.items():
            if key == 'random_seed':
                os.environ['RANDOM_SEED'] = str(value)
            elif key == 'n_jobs':
                os.environ['N_JOBS'] = str(value)
            elif key == 'verbose':
                os.environ['VERBOSE'] = str(value).lower()
            else:
                env_key = key.upper().replace('_', '_')
                os.environ[env_key] = str(value)
        
        return cls()

# Global configuration instance (singleton pattern)
_config: Optional[EnvConfig] = None

def get_config() -> EnvConfig:
    """
    Get the global configuration instance.
    
    Returns:
        EnvConfig instance
    """
    global _config
    if _config is None:
        _config = EnvConfig()
    return _config

def reset_config() -> None:
    """Reset the global configuration instance (useful for testing)."""
    global _config
    _config = None

def main():
    """Main entry point for command-line usage."""
    import sys
    
    config = get_config()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--json':
        # Output as JSON for scripting
        print(json.dumps(config.to_dict(), indent=2))
    else:
        # Human-readable output
        print("Project Configuration:")
        print(f"  Project Root: {config.project_root}")
        print(f"  Data Root: {config.data_root}")
        print(f"  Data Raw: {config.data_raw}")
        print(f"  Data Processed: {config.data_processed}")
        print(f"  Data Results: {config.data_results}")
        print(f"  Data Models: {config.data_models}")
        print(f"  Specs Root: {config.specs_root}")
        print(f"  Random Seed: {config.random_seed}")
        print(f"  N Jobs: {config.n_jobs}")
        print(f"  Verbose: {config.verbose}")

if __name__ == '__main__':
    main()
