import os
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, Optional, List, Tuple
from dataclasses import dataclass, field, asdict, fields

from src.utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class EnvironmentConfig:
    """Environment and hardware configuration."""
    cpu_only: bool = True
    num_threads: int = 4
    memory_limit_gb: float = 6.0
    timeout_hours: float = 4.0
    seed: int = 42

@dataclass
class DataConfig:
    """Data paths and loading configuration."""
    raw_dir: str = "data/raw"
    curated_dir: str = "data/curated"
    eval_dir: str = "data/eval"
    validation_dir: str = "data/validation"
    control_dir: str = "data/control"
    prompts_path: str = "data/prompts.jsonl"
    batch_size: int = 8
    num_workers: int = 2
    pin_memory: bool = False

@dataclass
class GenerationConfig:
    """Video generation configuration."""
    model_id: str = "Wan-AI/Wan2.1-Turbo"
    resolution: Tuple[int, int] = (512, 512)
    num_frames: int = 16
    guidance_scale: float = 7.5
    num_inference_steps: int = 20
    offload_to_kaggle: bool = False

@dataclass
class FilteringConfig:
    """Physics filtering configuration."""
    filter_discard_percent: float = 20.0
    continuity_threshold: float = 0.6
    contact_threshold: float = 0.6
    score_file: str = "data/curated/scores.parquet"

@dataclass
class TrainingConfig:
    """Model training configuration."""
    model_channels: int = 64
    num_down_blocks: int = 4
    num_up_blocks: int = 4
    attention_heads: int = 8
    target_param_count_m: int = 50
    learning_rate: float = 1e-4
    weight_decay: float = 1e-2
    num_epochs: int = 10
    save_interval: int = 1
    checkpoint_dir: str = "models/checkpoints"
    max_param_count_m: float = 60.0  # 10% tolerance
    min_param_count_m: float = 45.0  # 10% tolerance

@dataclass
class EvaluationConfig:
    """Evaluation configuration."""
    eval_set_size: int = 30
    r_bench_path: str = "data/eval/r_bench.json"
    pai_bench_path: str = "data/eval/pai_bench.json"
    baseline_path: str = "data/eval/physisforcing_baseline.json"
    results_path: str = "data/eval/results.json"
    correlation_threshold: float = 0.95

@dataclass
class LoggingConfig:
    """Logging configuration."""
    log_dir: str = "logs"
    log_level: str = "INFO"
    json_log: bool = True
    metrics_log: str = "logs/metrics.jsonl"
    discard_rate_log: str = "logs/discard_rate.log"
    orthogonality_log: str = "logs/orthogonality_gate.log"

@dataclass
class ProjectConfig:
    """Project-wide configuration."""
    project_id: str = "PROJ-951-llmxive-follow-up-extending-physisforcin"
    root_dir: str = "projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code"
    version: str = "1.0.0"

@dataclass
class Config:
    """Master configuration class containing all sub-configurations."""
    environment: EnvironmentConfig = field(default_factory=EnvironmentConfig)
    data: DataConfig = field(default_factory=DataConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    filtering: FilteringConfig = field(default_factory=FilteringConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    project: ProjectConfig = field(default_factory=ProjectConfig)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "environment": asdict(self.environment),
            "data": asdict(self.data),
            "generation": asdict(self.generation),
            "filtering": asdict(self.filtering),
            "training": asdict(self.training),
            "evaluation": asdict(self.evaluation),
            "logging": asdict(self.logging),
            "project": asdict(self.project),
        }

def create_default_config() -> Config:
    """Create a default configuration with standard values."""
    return Config()

def get_default_config() -> Config:
    """Get a fresh default configuration."""
    return create_default_config()

def validate_config_schema(config_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate that a config dictionary has the required structure and types."""
    errors = []
    required_sections = [
        "environment", "data", "generation", "filtering",
        "training", "evaluation", "logging", "project"
    ]
    
    for section in required_sections:
        if section not in config_dict:
            errors.append(f"Missing required section: {section}")
    
    if "filtering" in config_dict:
        if "filter_discard_percent" not in config_dict["filtering"]:
            errors.append("Missing filter_discard_percent in filtering section")
        else:
            val = config_dict["filtering"]["filter_discard_percent"]
            if not isinstance(val, (int, float)) or not (0 <= val <= 100):
                errors.append("filter_discard_percent must be a number between 0 and 100")
    
    if "environment" in config_dict:
        if "cpu_only" in config_dict["environment"]:
            if not isinstance(config_dict["environment"]["cpu_only"], bool):
                errors.append("cpu_only must be a boolean")
    
    return len(errors) == 0, errors

def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from a YAML file or return defaults."""
    config = create_default_config()
    
    if config_path is None:
        # Look for default config file
        default_paths = [
            "config.yaml",
            "projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/config.yaml",
        ]
        for path in default_paths:
            if Path(path).exists():
                config_path = path
                break
    
    if config_path and Path(config_path).exists():
        logger.info(f"Loading config from {config_path}")
        try:
            with open(config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
            
            is_valid, errors = validate_config_schema(config_dict)
            if not is_valid:
                logger.warning(f"Config validation warnings: {errors}")
            
            # Update environment
            if "environment" in config_dict:
                for key, value in config_dict["environment"].items():
                    if hasattr(config.environment, key):
                        setattr(config.environment, key, value)
            
            # Update data
            if "data" in config_dict:
                for key, value in config_dict["data"].items():
                    if hasattr(config.data, key):
                        setattr(config.data, key, value)
            
            # Update generation
            if "generation" in config_dict:
                for key, value in config_dict["generation"].items():
                    if hasattr(config.generation, key):
                        setattr(config.generation, key, value)
            
            # Update filtering
            if "filtering" in config_dict:
                for key, value in config_dict["filtering"].items():
                    if hasattr(config.filtering, key):
                        setattr(config.filtering, key, value)
            
            # Update training
            if "training" in config_dict:
                for key, value in config_dict["training"].items():
                    if hasattr(config.training, key):
                        setattr(config.training, key, value)
            
            # Update evaluation
            if "evaluation" in config_dict:
                for key, value in config_dict["evaluation"].items():
                    if hasattr(config.evaluation, key):
                        setattr(config.evaluation, key, value)
            
            # Update logging
            if "logging" in config_dict:
                for key, value in config_dict["logging"].items():
                    if hasattr(config.logging, key):
                        setattr(config.logging, key, value)
            
            # Update project
            if "project" in config_dict:
                for key, value in config_dict["project"].items():
                    if hasattr(config.project, key):
                        setattr(config.project, key, value)
                        
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse config YAML: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
    else:
        logger.info("No config file found, using defaults")
    
    return config

def save_config(config: Config, config_path: str) -> None:
    """Save configuration to a YAML file."""
    config_dict = config.to_dict()
    with open(config_path, 'w') as f:
        yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Saved config to {config_path}")

def get_filter_discard_threshold(config: Optional[Config] = None) -> float:
    """Get the filter discard threshold from config."""
    if config is None:
        config = get_default_config()
    return config.filtering.filter_discard_percent

def get_config() -> Config:
    """Global accessor for configuration."""
    return load_config()

def main():
    """Main entry point for config module testing."""
    config = load_config()
    print(f"Loaded config:")
    print(f"  CPU Only: {config.environment.cpu_only}")
    print(f"  Memory Limit: {config.environment.memory_limit_gb} GB")
    print(f"  Discard Percent: {config.filtering.filter_discard_percent}%")
    print(f"  Target Params: {config.training.target_param_count_m}M")

if __name__ == "__main__":
    main()