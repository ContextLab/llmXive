"""
Configuration management for the plant VOC prediction pipeline.

Handles loading environment variables from .env files, validating paths,
and managing random seeds for reproducibility.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Global configuration state
_config: Optional['ProjectConfig'] = None

class ConfigError(Exception):
    """Raised when configuration validation fails."""
    pass

class ProjectConfig:
    """
    Container for project configuration loaded from environment variables.
    
    Expected Environment Variables:
    - DATA_RAW_PATH: Directory for raw data files
    - DATA_PROCESSED_PATH: Directory for processed data files
    - DATA_RESULTS_PATH: Directory for analysis results
    - DATA_MODELS_PATH: Directory for trained model artifacts
    - RANDOM_SEED: Integer seed for reproducibility (default: 42)
    - LOG_LEVEL: Logging verbosity (default: INFO)
    """
    
    def __init__(self, env_path: Optional[Path] = None):
        """
        Initialize configuration by loading from .env file.
        
        Args:
            env_path: Path to .env file. If None, searches in project root.
        """
        # Load environment variables
        if env_path and env_path.exists():
            load_dotenv(env_path)
        else:
            # Default search path: project root
            default_env = Path(__file__).parent.parent.parent / ".env"
            if default_env.exists():
                load_dotenv(default_env)
        
        # Validate required paths
        self.data_raw_path = self._get_path("DATA_RAW_PATH", "data/raw")
        self.data_processed_path = self._get_path("DATA_PROCESSED_PATH", "data/processed")
        self.data_results_path = self._get_path("DATA_RESULTS_PATH", "data/results")
        self.data_models_path = self._get_path("DATA_MODELS_PATH", "data/models")
        
        # Validate and set random seed
        self.random_seed = self._get_int("RANDOM_SEED", 42)
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _get_path(self, key: str, default: str) -> Path:
        """Get and validate a path from environment variable."""
        path_str = os.getenv(key, default)
        path = Path(path_str)
        
        # Make absolute if relative
        if not path.is_absolute():
            # Assume relative to project root (parent of code/)
            project_root = Path(__file__).parent.parent.parent
            path = (project_root / path).resolve()
        
        return path
    
    def _get_int(self, key: str, default: int) -> int:
        """Get and validate an integer from environment variable."""
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            raise ConfigError(f"Invalid integer value for {key}: {value}")
    
    def _ensure_directories(self):
        """Create data directories if they don't exist."""
        for path in [
            self.data_raw_path,
            self.data_processed_path,
            self.data_results_path,
            self.data_models_path
        ]:
            path.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as a dictionary."""
        return {
            "data_raw_path": str(self.data_raw_path),
            "data_processed_path": str(self.data_processed_path),
            "data_results_path": str(self.data_results_path),
            "data_models_path": str(self.data_models_path),
            "random_seed": self.random_seed,
            "log_level": self.log_level
        }
    
    def __repr__(self) -> str:
        return f"ProjectConfig(seed={self.random_seed}, log_level={self.log_level})"

def get_config(env_path: Optional[Path] = None) -> ProjectConfig:
    """
    Get the global project configuration.
    
    Args:
        env_path: Optional path to .env file.
        
    Returns:
        ProjectConfig instance
    """
    global _config
    if _config is None:
        _config = ProjectConfig(env_path)
    return _config

def reset_config() -> None:
    """Reset the global configuration (useful for testing)."""
    global _config
    _config = None

# Convenience function for scripts
def main():
    """Print current configuration to stdout."""
    config = get_config()
    import json
    print(json.dumps(config.to_dict(), indent=2))

if __name__ == "__main__":
    main()
