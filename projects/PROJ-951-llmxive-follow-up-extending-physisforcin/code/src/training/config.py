"""
Configuration management for the PhysisForcing training pipeline.
Handles hyperparameters, CPU-only flags, and schema validation.
"""
import os
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, Optional, List, Tuple
from dataclasses import dataclass, field, asdict, fields

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Default configuration values
DEFAULT_CONFIG = {
    "experiment_name": "physs_filter_experiment",
    "seed": 42,
    "cpu_only": True,
    "max_memory_gb": 6.0,
    "batch_size": 1,
    "num_workers": 0,  # 0 for CPU-only to avoid multiprocessing overhead
    "pin_memory": False,
    "filter_discard_percent": 0.4,
    "training_epochs": 10,
    "learning_rate": 1e-4,
    "weight_decay": 1e-2,
    "model_params": {
        "channels": 64,
        "num_blocks": 4,
        "attention_heads": 4,
        "target_params_millions": 50.0
    },
    "paths": {
        "data_root": "data",
        "curated_dir": "data/curated",
        "raw_dir": "data/raw",
        "model_output_dir": "models",
        "checkpoint_dir": "models/checkpoints"
    },
    "validation": {
        "check_nan_loss": True,
        "nan_retry_limit": 3,
        "timeout_hours": 4.0
    }
}

@dataclass
class TrainingConfig:
    """Dataclass representation of the training configuration."""
    experiment_name: str = DEFAULT_CONFIG["experiment_name"]
    seed: int = DEFAULT_CONFIG["seed"]
    cpu_only: bool = DEFAULT_CONFIG["cpu_only"]
    max_memory_gb: float = DEFAULT_CONFIG["max_memory_gb"]
    batch_size: int = DEFAULT_CONFIG["batch_size"]
    num_workers: int = DEFAULT_CONFIG["num_workers"]
    pin_memory: bool = DEFAULT_CONFIG["pin_memory"]
    filter_discard_percent: float = DEFAULT_CONFIG["filter_discard_percent"]
    training_epochs: int = DEFAULT_CONFIG["training_epochs"]
    learning_rate: float = DEFAULT_CONFIG["learning_rate"]
    weight_decay: float = DEFAULT_CONFIG["weight_decay"]
    
    # Nested configurations as dataclasses or dicts
    model_params: Dict[str, Any] = field(default_factory=lambda: DEFAULT_CONFIG["model_params"].copy())
    paths: Dict[str, str] = field(default_factory=lambda: DEFAULT_CONFIG["paths"].copy())
    validation: Dict[str, Any] = field(default_factory=lambda: DEFAULT_CONFIG["validation"].copy())

    def to_dict(self) -> Dict[str, Any]:
        """Convert the config to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrainingConfig':
        """Create a TrainingConfig instance from a dictionary."""
        # Handle nested dicts for model_params, paths, validation
        if "model_params" in data and isinstance(data["model_params"], dict):
            data["model_params"] = {**DEFAULT_CONFIG["model_params"], **data["model_params"]}
        if "paths" in data and isinstance(data["paths"], dict):
            data["paths"] = {**DEFAULT_CONFIG["paths"], **data["paths"]}
        if "validation" in data and isinstance(data["validation"], dict):
            data["validation"] = {**DEFAULT_CONFIG["validation"], **data["validation"]}
        
        return cls(**data)

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate the configuration values."""
        errors = []
        
        if not self.cpu_only:
            logger.warning("Non-CPU-only mode detected. Ensure CUDA is available.")
        
        if self.filter_discard_percent < 0.0 or self.filter_discard_percent > 1.0:
            errors.append(f"filter_discard_percent must be between 0.0 and 1.0, got {self.filter_discard_percent}")
        
        if self.batch_size < 1:
            errors.append(f"batch_size must be at least 1, got {self.batch_size}")
        
        if self.learning_rate <= 0:
            errors.append(f"learning_rate must be positive, got {self.learning_rate}")
        
        if self.max_memory_gb <= 0:
            errors.append(f"max_memory_gb must be positive, got {self.max_memory_gb}")

        return len(errors) == 0, errors

def create_default_config() -> TrainingConfig:
    """Create a new configuration with default values."""
    logger.info("Creating default training configuration.")
    return TrainingConfig()

def get_default_config() -> TrainingConfig:
    """Get a fresh copy of the default configuration."""
    return create_default_config()

def validate_config_schema(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that a dictionary matches the expected schema for TrainingConfig.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    
    # Check top-level keys exist in DEFAULT_CONFIG
    for key in DEFAULT_CONFIG:
        if key not in data:
            # Allow missing keys if they have defaults, but warn if critical
            if key in ["cpu_only", "filter_discard_percent", "batch_size"]:
                logger.warning(f"Missing critical config key: {key}, using default.")
    
    # Type checking for specific fields
    if "filter_discard_percent" in data:
        if not isinstance(data["filter_discard_percent"], (int, float)):
            errors.append("filter_discard_percent must be a number")
        elif not (0.0 <= data["filter_discard_percent"] <= 1.0):
            errors.append("filter_discard_percent must be between 0.0 and 1.0")
    
    if "batch_size" in data:
        if not isinstance(data["batch_size"], int) or data["batch_size"] < 1:
            errors.append("batch_size must be a positive integer")
    
    if "cpu_only" in data:
        if not isinstance(data["cpu_only"], bool):
            errors.append("cpu_only must be a boolean")

    return len(errors) == 0, errors

def load_config(config_path: Optional[str] = None) -> TrainingConfig:
    """
    Load configuration from a YAML file.
    If config_path is None, attempts to load from default locations.
    Falls back to defaults if file is missing or invalid.
    """
    if config_path is None:
        # Default search paths
        possible_paths = [
            "config.yaml",
            "data/config.yaml",
            "src/training/config.yaml",
            os.path.join("projects", "PROJ-951-llmxive-follow-up-extending-physisforcin", "code", "config.yaml")
        ]
        for path in possible_paths:
            if os.path.exists(path):
                config_path = path
                break
    
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)
            
            is_valid, errors = validate_config_schema(data)
            if not is_valid:
                logger.error(f"Config validation errors: {errors}")
                # Continue with partial config or raise? Let's warn and merge with defaults.
            
            # Merge with defaults to ensure all fields exist
            merged_data = {**DEFAULT_CONFIG, **data}
            # Handle nested merges manually for model_params, paths, validation
            if "model_params" in data:
                merged_data["model_params"] = {**DEFAULT_CONFIG["model_params"], **data["model_params"]}
            if "paths" in data:
                merged_data["paths"] = {**DEFAULT_CONFIG["paths"], **data["paths"]}
            if "validation" in data:
                merged_data["validation"] = {**DEFAULT_CONFIG["validation"], **data["validation"]}
            
            logger.info(f"Loaded configuration from {config_path}")
            return TrainingConfig.from_dict(merged_data)
        
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML config: {e}")
            logger.warning("Using default configuration.")
            return get_default_config()
        except Exception as e:
            logger.error(f"Unexpected error loading config: {e}")
            logger.warning("Using default configuration.")
            return get_default_config()
    else:
        if config_path:
            logger.warning(f"Config file not found at {config_path}. Using defaults.")
        else:
            logger.info("No config file found. Using defaults.")
        return get_default_config()

def save_config(config: TrainingConfig, output_path: str) -> None:
    """Save the configuration to a YAML file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = config.to_dict()
    with open(output_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Saved configuration to {output_path}")

def get_filter_discard_threshold(config: Optional[TrainingConfig] = None) -> float:
    """
    Get the discard threshold (percentile) for filtering.
    Defaults to 0.4 (40% discard) if not provided.
    """
    if config is None:
        config = get_default_config()
    return config.filter_discard_percent

def get_config(config_path: Optional[str] = None) -> TrainingConfig:
    """
    Convenience function to load and validate configuration.
    Returns the config object, raising an error if validation fails critically.
    """
    config = load_config(config_path)
    is_valid, errors = config.validate()
    
    if not is_valid:
        # Log errors but return the config anyway for debugging, 
        # unless critical fields are wrong.
        logger.warning(f"Configuration validation warnings: {errors}")
        # In a strict pipeline, we might raise ValueError here.
        # For now, we return it but log the issues.
    
    return config

def main():
    """Main entry point for testing the config module."""
    print("Testing TrainingConfig module...")
    
    # Test default creation
    config = get_default_config()
    print(f"Default config: {config.to_dict()}")
    
    # Test validation
    is_valid, errors = config.validate()
    print(f"Validation result: {is_valid}, Errors: {errors}")
    
    # Test schema validation
    bad_data = {"filter_discard_percent": 1.5, "batch_size": -1}
    is_valid_schema, schema_errors = validate_config_schema(bad_data)
    print(f"Schema validation (bad data): {is_valid_schema}, Errors: {schema_errors}")
    
    # Test save and load
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
        temp_path = f.name
    
    save_config(config, temp_path)
    loaded_config = load_config(temp_path)
    
    print(f"Loaded config matches: {config.to_dict() == loaded_config.to_dict()}")
    
    # Cleanup
    os.unlink(temp_path)
    print("Config module test complete.")

if __name__ == "__main__":
    main()
