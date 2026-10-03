import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml

class Config:
    """
    Base configuration loader for environment variables and paths.
    
    Handles loading configuration from:
    1. Environment variables (highest priority)
    2. YAML configuration file (config.yaml in project root)
    3. Default values (lowest priority)
    
    Includes configurable join_radius_km parameter with default 10km
    based on WorldClim resolution for reproducibility.
    """
    
    # Default paths relative to project root
    DEFAULT_DATA_DIR = "data"
    DEFAULT_CODE_DIR = "code"
    DEFAULT_TESTS_DIR = "tests"
    DEFAULT_STATE_DIR = "state/projects"
    
    # Default configuration values
    DEFAULT_JOIN_RADIUS_KM = 10.0  # Based on WorldClim v2.1 resolution
    DEFAULT_MAX_RECORDS = None  # None means no limit
    DEFAULT_LOG_LEVEL = "INFO"
    
    def __init__(
        self,
        config_path: Optional[Path] = None,
        data_dir: Optional[str] = None,
        code_dir: Optional[str] = None,
        tests_dir: Optional[str] = None,
        join_radius_km: Optional[float] = None,
        max_records: Optional[int] = None,
        log_level: Optional[str] = None
    ):
        """
        Initialize configuration with environment variables, file, and defaults.
        
        Args:
            config_path: Path to YAML config file (default: config.yaml in root)
            data_dir: Override for data directory path
            code_dir: Override for code directory path
            tests_dir: Override for tests directory path
            join_radius_km: Override for spatial join radius in km (default: 10.0)
            max_records: Override for maximum records to process
            log_level: Override for logging level
        """
        self._config: Dict[str, Any] = {}
        
        # Load from YAML config file if exists
        if config_path is None:
            # Try common locations
            possible_paths = [
                Path("config.yaml"),
                Path("config.yml"),
                Path("./config.yaml"),
                Path("./config.yml")
            ]
            for p in possible_paths:
                if p.exists():
                    config_path = p
                    break
        
        if config_path and Path(config_path).exists():
            self._load_from_yaml(Path(config_path))
        
        # Override with environment variables
        self._load_from_env()
        
        # Apply explicit overrides
        if data_dir is not None:
            self._config["data_dir"] = data_dir
        if code_dir is not None:
            self._config["code_dir"] = code_dir
        if tests_dir is not None:
            self._config["tests_dir"] = tests_dir
        if join_radius_km is not None:
            self._config["join_radius_km"] = join_radius_km
        if max_records is not None:
            self._config["max_records"] = max_records
        if log_level is not None:
            self._config["log_level"] = log_level
        
        # Set defaults for missing values
        self._set_defaults()
        
        # Resolve paths to absolute
        self._resolve_paths()
    
    def _load_from_yaml(self, config_path: Path) -> None:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f) or {}
                self._config.update(file_config)
        except Exception as e:
            # Log warning but continue with other sources
            print(f"Warning: Could not load config from {config_path}: {e}")
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        env_mappings = {
            "DATA_DIR": "data_dir",
            "CODE_DIR": "code_dir",
            "TESTS_DIR": "tests_dir",
            "JOIN_RADIUS_KM": "join_radius_km",
            "MAX_RECORDS": "max_records",
            "LOG_LEVEL": "log_level"
        }
        
        for env_var, config_key in env_mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Try to convert to appropriate type
                if config_key in ["join_radius_km", "max_records"]:
                    try:
                        value = float(value) if config_key == "join_radius_km" else int(value)
                    except ValueError:
                        pass  # Keep as string if conversion fails
                self._config[config_key] = value
    
    def _set_defaults(self) -> None:
        """Set default values for missing configuration."""
        defaults = {
            "data_dir": self.DEFAULT_DATA_DIR,
            "code_dir": self.DEFAULT_CODE_DIR,
            "tests_dir": self.DEFAULT_TESTS_DIR,
            "join_radius_km": self.DEFAULT_JOIN_RADIUS_KM,
            "max_records": self.DEFAULT_MAX_RECORDS,
            "log_level": self.DEFAULT_LOG_LEVEL
        }
        
        for key, value in defaults.items():
            if key not in self._config:
                self._config[key] = value
    
    def _resolve_paths(self) -> None:
        """Resolve relative paths to absolute paths."""
        path_keys = ["data_dir", "code_dir", "tests_dir"]
        project_root = Path.cwd()
        
        for key in path_keys:
            if key in self._config:
                path = Path(self._config[key])
                if not path.is_absolute():
                    path = project_root / path
                self._config[key] = str(path)
        
        # Ensure state directory path is set
        if "state_dir" not in self._config:
            self._config["state_dir"] = str(project_root / self.DEFAULT_STATE_DIR)
    
    @property
    def data_dir(self) -> Path:
        """Get data directory as Path object."""
        return Path(self._config["data_dir"])
    
    @property
    def code_dir(self) -> Path:
        """Get code directory as Path object."""
        return Path(self._config["code_dir"])
    
    @property
    def tests_dir(self) -> Path:
        """Get tests directory as Path object."""
        return Path(self._config["tests_dir"])
    
    @property
    def state_dir(self) -> Path:
        """Get state directory as Path object."""
        return Path(self._config.get("state_dir", Path.cwd() / self.DEFAULT_STATE_DIR))
    
    @property
    def join_radius_km(self) -> float:
        """Get spatial join radius in kilometers."""
        return float(self._config["join_radius_km"])
    
    @property
    def max_records(self) -> Optional[int]:
        """Get maximum records limit."""
        val = self._config.get("max_records")
        return int(val) if val is not None else None
    
    @property
    def log_level(self) -> str:
        """Get logging level."""
        return self._config.get("log_level", "INFO")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return self._config.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary."""
        return self._config.copy()
    
    def __repr__(self) -> str:
        return f"Config(join_radius_km={self.join_radius_km}, data_dir={self.data_dir})"


def load_config(config_path: Optional[Path] = None, **overrides) -> Config:
    """
    Convenience function to load configuration with optional overrides.
    
    Args:
        config_path: Path to YAML config file
        **overrides: Any Config constructor arguments
        
    Returns:
        Config instance
    """
    return Config(config_path=config_path, **overrides)