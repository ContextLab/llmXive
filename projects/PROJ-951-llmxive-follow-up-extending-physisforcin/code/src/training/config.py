"""
Configuration management for the PhysisForcing pipeline.
Handles hyperparameters, CPU-only flags, and schema validation.
"""
import os
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, Optional, List, Tuple
from dataclasses import dataclass, field, asdict, fields

# Configure logger
logger = logging.getLogger(__name__)

@dataclass
class EnvironmentConfig:
    cpu_only: bool = True
    cuda_enabled: bool = False
    max_ram_gb: float = 6.0
    max_disk_gb: float = 14.0

@dataclass
class DataConfig:
    root: str = "data"
    raw: str = "data/raw"
    curated: str = "data/curated"
    eval: str = "data/eval"
    validation: str = "data/validation"
    control: str = "data/control"
    prompts: str = "data/prompts.json"

@dataclass
class GenerationConfig:
    model_id: str = "Wan-AI/Wan2.1-Turbo"
    device: str = "cpu"
    offload_to_kaggle: bool = True
    max_videos: int = 100
    frame_rate: int = 8
    resolution: Dict[str, int] = field(default_factory=lambda: {"width": 512, "height": 512})
    timeout_seconds: int = 3600

@dataclass
class FilteringConfig:
    # Explicitly set to 0.4 to resolve FR-003
    filter_discard_percent: float = 0.4
    physics_engine: str = "pybullet"
    simulation_steps: int = 100
    continuity_threshold: float = 0.6
    contact_threshold: float = 0.5
    headless_mode: bool = True

@dataclass
class TrainingConfig:
    model_type: str = "unet"
    base_channels: int = 64
    down_blocks: int = 4
    up_blocks: int = 4
    attention_heads: int = 8
    estimated_params_m: int = 50
    batch_size: int = 4
    learning_rate: float = 1e-4
    epochs: int = 10
    seed: int = 42
    checkpoint_interval: int = 1000
    timeout_hours: int = 4

@dataclass
class EvaluationConfig:
    eval_set_size: int = 30
    statistical_test: str = "mann_whitney_u"
    significance_level: float = 0.05
    baseline_source: str = "physisforcing_paper"
    mu_joco_validation: bool = True

@dataclass
class LoggingConfig:
    level: str = "INFO"
    format: str = "json"
    log_dir: str = "logs"
    metrics_file: str = "metrics.jsonl"
    rotation_max_mb: int = 10
    rotation_backup_count: int = 5

@dataclass
class ProjectConfig:
    project_id: str = "PROJ-951-llmxive-follow-up-extending-physisforcin"
    version: str = "1.0.0"
    description: str = "Physics-informed filtering for synthetic robotic video datasets"
    environment: EnvironmentConfig = field(default_factory=EnvironmentConfig)
    data: DataConfig = field(default_factory=DataConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    filtering: FilteringConfig = field(default_factory=FilteringConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

def create_default_config() -> ProjectConfig:
    """Create a default configuration object."""
    return ProjectConfig()

def get_default_config() -> Dict[str, Any]:
    """Return a dictionary representation of the default configuration."""
    return asdict(create_default_config())

def validate_config_schema(config_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate the configuration dictionary against the expected schema.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    required_keys = [
        "project_id",
        "environment.cpu_only",
        "data.root",
        "filtering.filter_discard_percent",
        "training.seed"
    ]

    # Check required keys
    for key in required_keys:
        keys = key.split(".")
        current = config_dict
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                errors.append(f"Missing required key: {key}")
                break

    # Type checks
    type_checks = {
        "filtering.filter_discard_percent": float,
        "training.epochs": int,
        "environment.max_ram_gb": float
    }

    for key, expected_type in type_checks.items():
        keys = key.split(".")
        current = config_dict
        found = True
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                found = False
                break
        
        if found and not isinstance(current, expected_type):
            errors.append(f"Type mismatch for {key}: expected {expected_type.__name__}, got {type(current).__name__}")

    # Value ranges
    value_ranges = {
        "filtering.filter_discard_percent": (0.0, 1.0),
        "training.batch_size": (1, 128)
    }

    for key, (min_val, max_val) in value_ranges.items():
        keys = key.split(".")
        current = config_dict
        found = True
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                found = False
                break

        if found:
            if not (min_val <= current <= max_val):
                errors.append(f"Value out of range for {key}: {current} not in [{min_val}, {max_val}]")

    return len(errors) == 0, errors

def load_config(config_path: Optional[str] = None) -> ProjectConfig:
    """Load configuration from a YAML file."""
    if config_path is None:
        config_path = "code/config.yaml"
    
    path = Path(config_path)
    if not path.exists():
        logger.warning(f"Config file {config_path} not found. Using defaults.")
        return create_default_config()

    try:
        with open(path, 'r') as f:
            config_dict = yaml.safe_load(f)
        
        is_valid, errors = validate_config_schema(config_dict)
        if not is_valid:
            logger.error(f"Config validation failed: {errors}")
            # Fallback to defaults if validation fails
            return create_default_config()

        # Map dictionary to dataclass
        config = ProjectConfig()
        
        # Helper to set nested values
        def set_nested(obj, keys, value):
            if len(keys) == 1:
                if hasattr(obj, keys[0]):
                    setattr(obj, keys[0], value)
            else:
                child = getattr(obj, keys[0])
                set_nested(child, keys[1:], value)

        def process_dict(d, obj):
            for key, value in d.items():
                if hasattr(obj, key):
                    attr = getattr(obj, key)
                    if isinstance(attr, dict) and isinstance(value, dict):
                        process_dict(value, attr)
                    elif not isinstance(attr, dict):
                        set_nested(obj, [key], value)

        process_dict(config_dict, config)
        return config

    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return create_default_config()

def save_config(config: ProjectConfig, config_path: str) -> bool:
    """Save configuration to a YAML file."""
    try:
        config_dict = asdict(config)
        with open(config_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False)
        return True
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return False

def get_filter_discard_threshold(config: ProjectConfig) -> float:
    """Get the filter discard threshold from the configuration."""
    return config.filtering.filter_discard_percent

def get_config(config_path: Optional[str] = None) -> ProjectConfig:
    """Convenience function to load and return the config."""
    return load_config(config_path)

def main():
    """Main entry point for testing configuration loading."""
    config = get_config()
    print(f"Loaded config for project: {config.project_id}")
    print(f"Filter discard percent: {config.filtering.filter_discard_percent}")
    print(f"CPU Only: {config.environment.cpu_only}")
    print(f"Training epochs: {config.training.epochs}")

if __name__ == "__main__":
    main()
