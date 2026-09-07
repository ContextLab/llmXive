"""
Base configuration loader for environment variables and dataset paths.

This module provides a centralized way to load and validate configuration
from environment variables and default paths. It ensures that all necessary
paths exist and are accessible before the pipeline proceeds.
"""
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class Config:
    """
    Central configuration object for the llmXive pipeline.
    
    Attributes:
        project_root: The root directory of the project.
        data_root: Root directory for all data files.
        raw_data_dir: Directory for raw downloaded datasets.
        processed_data_dir: Directory for processed data artifacts.
        graphs_dir: Directory for dependency graph JSON files.
        models_dir: Directory for trained models and thresholds.
        contracts_dir: Directory for YAML schema files.
        state_dir: Directory for project state tracking.
        datasets: Dictionary mapping dataset names to their specific paths.
        timeout_seconds: Default timeout for baseline execution.
        max_workers: Maximum number of parallel workers for processing.
        environment: Current environment (development, production, etc.)
    """
    project_root: Path
    data_root: Path
    raw_data_dir: Path
    processed_data_dir: Path
    graphs_dir: Path
    models_dir: Path
    contracts_dir: Path
    state_dir: Path
    datasets: Dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 300
    max_workers: int = 4
    environment: str = "development"

    def __post_init__(self):
        """Validate and create directories if they don't exist."""
        self._validate_and_create_dirs()

    def _validate_and_create_dirs(self):
        """Ensure all required directories exist."""
        required_dirs = [
            self.raw_data_dir,
            self.processed_data_dir,
            self.graphs_dir,
            self.models_dir,
            self.contracts_dir,
            self.state_dir,
        ]

        for dir_path in required_dirs:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
            elif not dir_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {dir_path}")

    def get_dataset_path(self, dataset_name: str) -> Optional[Path]:
        """Get the path for a specific dataset by name."""
        if dataset_name in self.datasets:
            return Path(self.datasets[dataset_name])
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to a dictionary for serialization."""
        return {
            "project_root": str(self.project_root),
            "data_root": str(self.data_root),
            "raw_data_dir": str(self.raw_data_dir),
            "processed_data_dir": str(self.processed_data_dir),
            "graphs_dir": str(self.graphs_dir),
            "models_dir": str(self.models_dir),
            "contracts_dir": str(self.contracts_dir),
            "state_dir": str(self.state_dir),
            "datasets": self.datasets,
            "timeout_seconds": self.timeout_seconds,
            "max_workers": self.max_workers,
            "environment": self.environment,
        }


def _get_env_path(key: str, default: Optional[str] = None) -> Optional[Path]:
    """Get a path from an environment variable."""
    value = os.getenv(key, default)
    if value:
        return Path(value)
    return None


def _get_env_int(key: str, default: int) -> int:
    """Get an integer from an environment variable."""
    value = os.getenv(key)
    if value:
        try:
            return int(value)
        except ValueError:
            raise ValueError(f"Environment variable {key} must be an integer, got: {value}")
    return default


def _get_env_str(key: str, default: str) -> str:
    """Get a string from an environment variable."""
    return os.getenv(key, default)


def _load_datasets_from_env() -> Dict[str, str]:
    """Load dataset paths from environment variables."""
    datasets = {}
    
    # Check for specific dataset paths
    for dataset_name in ["swe_bench", "agent_bench"]:
        env_key = f"DATASET_{dataset_name.upper()}_PATH"
        path = os.getenv(env_key)
        if path:
            datasets[dataset_name] = path
    
    # Also support a generic DATASETS_JSON if multiple are defined
    datasets_json = os.getenv("DATASETS_JSON")
    if datasets_json:
        import json
        try:
            extra_datasets = json.loads(datasets_json)
            datasets.update(extra_datasets)
        except json.JSONDecodeError:
            raise ValueError("DATASETS_JSON environment variable contains invalid JSON")
    
    return datasets


def get_config() -> Config:
    """
    Load configuration from environment variables with sensible defaults.
    
    This function is the primary entry point for accessing configuration
    throughout the pipeline. It reads from environment variables and
    falls back to project-relative defaults.
    
    Returns:
        Config: A validated configuration object.
    
    Raises:
        RuntimeError: If required directories cannot be created or validated.
        ValueError: If environment variable values are invalid.
    """
    # Determine project root (parent of 'code' directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    
    # Default paths relative to project root
    data_root = project_root / "data"
    raw_data_dir = data_root / "raw"
    processed_data_dir = data_root / "processed"
    graphs_dir = data_root / "graphs"
    models_dir = project_root / "models"
    contracts_dir = project_root / "contracts"
    state_dir = project_root / "state"
    
    # Load from environment if set
    if env_root := _get_env_path("PROJECT_ROOT"):
        project_root = env_root
    if env_data := _get_env_path("DATA_ROOT"):
        data_root = env_data
        raw_data_dir = data_root / "raw"
        processed_data_dir = data_root / "processed"
        graphs_dir = data_root / "graphs"
    
    raw_data_dir = _get_env_path("RAW_DATA_DIR", str(raw_data_dir)) or raw_data_dir
    processed_data_dir = _get_env_path("PROCESSED_DATA_DIR", str(processed_data_dir)) or processed_data_dir
    graphs_dir = _get_env_path("GRAPHS_DIR", str(graphs_dir)) or graphs_dir
    models_dir = _get_env_path("MODELS_DIR", str(models_dir)) or models_dir
    contracts_dir = _get_env_path("CONTRACTS_DIR", str(contracts_dir)) or contracts_dir
    state_dir = _get_env_path("STATE_DIR", str(state_dir)) or state_dir
    
    # Load datasets
    datasets = _load_datasets_from_env()
    
    # Load other settings
    timeout_seconds = _get_env_int("EXECUTION_TIMEOUT_SECONDS", 300)
    max_workers = _get_env_int("MAX_WORKERS", 4)
    environment = _get_env_str("ENVIRONMENT", "development")
    
    config = Config(
        project_root=project_root,
        data_root=data_root,
        raw_data_dir=raw_data_dir,
        processed_data_dir=processed_data_dir,
        graphs_dir=graphs_dir,
        models_dir=models_dir,
        contracts_dir=contracts_dir,
        state_dir=state_dir,
        datasets=datasets,
        timeout_seconds=timeout_seconds,
        max_workers=max_workers,
        environment=environment,
    )
    
    return config


def validate_config(config: Config) -> bool:
    """
    Validate that the configuration is complete and paths are accessible.
    
    Args:
        config: The configuration object to validate.
    
    Returns:
        bool: True if valid, raises an exception otherwise.
    
    Raises:
        ValueError: If any required path is missing or invalid.
    """
    # Check that all directories exist and are writable
    required_dirs = [
        ("raw_data_dir", config.raw_data_dir),
        ("processed_data_dir", config.processed_data_dir),
        ("graphs_dir", config.graphs_dir),
        ("models_dir", config.models_dir),
        ("contracts_dir", config.contracts_dir),
        ("state_dir", config.state_dir),
    ]
    
    for name, path in required_dirs:
        if not path.exists():
            raise ValueError(f"Required directory does not exist: {name} ({path})")
        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {name} ({path})")
        if not os.access(path, os.W_OK):
            raise ValueError(f"Directory is not writable: {name} ({path})")
    
    # Validate timeout
    if config.timeout_seconds < 1:
        raise ValueError("timeout_seconds must be at least 1")
    
    # Validate workers
    if config.max_workers < 1:
        raise ValueError("max_workers must be at least 1")
    
    return True


# Convenience function for scripts that need config immediately
config_instance: Optional[Config] = None


def get_global_config() -> Config:
    """Get the global configuration instance, loading it if necessary."""
    global config_instance
    if config_instance is None:
        config_instance = get_config()
        validate_config(config_instance)
    return config_instance
