import os
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, Optional, List, Tuple
from dataclasses import dataclass, field, asdict, fields

@dataclass
class EnvironmentConfig:
    cpu_only: bool = True
    seed: int = 42
    max_memory_gb: float = 7.0

@dataclass
class DataConfig:
    raw_dir: str = "data/raw"
    curated_dir: str = "data/curated"
    eval_dir: str = "data/eval"
    validation_dir: str = "data/validation"
    control_dir: str = "data/control"
    prompts_file: str = "data/prompts.jsonl"

@dataclass
class GenerationConfig:
    model_id: str = "Wan-AI/Wan2.1-Turbo"
    batch_size: int = 1
    offload_enabled: bool = True
    offload_kaggle_key: Optional[str] = None

@dataclass
class FilteringConfig:
    discard_percentile: int = 40
    continuity_weight: float = 0.5
    contact_weight: float = 0.5
    min_score_threshold: float = 0.0

@dataclass
class TrainingConfig:
    model_type: str = "unet"
    base_channels: int = 64
    down_blocks: int = 3
    up_blocks: int = 3
    attention_heads: int = 8
    batch_size: int = 2
    learning_rate: float = 1.0e-4
    max_epochs: int = 10
    patience: int = 2
    quantization_8bit: bool = True
    gradient_checkpointing: bool = True
    timeout_seconds: int = 14400

@dataclass
class EvaluationConfig:
    r_bench_enabled: bool = True
    pai_bench_enabled: bool = True
    tost_margin: float = 0.15
    power_analysis_alpha: float = 0.05
    power_analysis_power: float = 0.80
    eval_sample_size: int = 30

@dataclass
class LoggingConfig:
    level: str = "INFO"
    log_dir: str = "logs"
    json_logs: bool = True
    rotation_max_mb: int = 100
    rotation_backup_count: int = 5

@dataclass
class ProjectConfig:
    name: str = "PROJ-951-llmxive-follow-up-extending-physisforcin"
    version: str = "0.1.0"
    root_dir: str = "."

@dataclass
class Config:
    project: ProjectConfig = field(default_factory=ProjectConfig)
    environment: EnvironmentConfig = field(default_factory=EnvironmentConfig)
    data: DataConfig = field(default_factory=DataConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    filter: FilteringConfig = field(default_factory=FilteringConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        config = cls()
        for key, value in data.items():
            if hasattr(config, key) and isinstance(getattr(config, key), object):
                sub_config_class = None
                if key == 'project': sub_config_class = ProjectConfig
                elif key == 'environment': sub_config_class = EnvironmentConfig
                elif key == 'data': sub_config_class = DataConfig
                elif key == 'generation': sub_config_class = GenerationConfig
                elif key == 'filter': sub_config_class = FilteringConfig
                elif key == 'training': sub_config_class = TrainingConfig
                elif key == 'evaluation': sub_config_class = EvaluationConfig
                elif key == 'logging': sub_config_class = LoggingConfig
                
                if sub_config_class:
                    if isinstance(value, dict):
                        for sub_key, sub_val in value.items():
                            if hasattr(getattr(config, key), sub_key):
                                setattr(getattr(config, key), sub_key, sub_val)
        return config

    def to_dict(self) -> Dict[str, Any]:
        return {
            'project': asdict(self.project),
            'environment': asdict(self.environment),
            'data': asdict(self.data),
            'generation': asdict(self.generation),
            'filter': asdict(self.filter),
            'training': asdict(self.training),
            'evaluation': asdict(self.evaluation),
            'logging': asdict(self.logging)
        }

def create_default_config() -> Config:
    return Config()

def get_default_config() -> Config:
    return create_default_config()

def validate_config_schema(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors = []
    required_keys = ['project', 'environment', 'data', 'generation', 'filter', 'training', 'evaluation', 'logging']
    for key in required_keys:
        if key not in data:
            errors.append(f"Missing required key: {key}")
    
    if 'filter' in data:
        if 'discard_percentile' not in data['filter']:
            errors.append("Missing required filter parameter: discard_percentile")
        else:
            val = data['filter']['discard_percentile']
            if not isinstance(val, int) or val < 0 or val > 100:
                errors.append("filter.discard_percentile must be an integer between 0 and 100")
    
    return len(errors) == 0, errors

def load_config(config_path: str) -> Config:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    
    is_valid, errors = validate_config_schema(data)
    if not is_valid:
        raise ValueError(f"Invalid config schema: {errors}")
    
    return Config.from_dict(data)

def save_config(config: Config, config_path: str) -> None:
    path = Path(config_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False)

def get_filter_discard_threshold(scores: List[float], config: Config) -> float:
    """
    Dynamically calculates the score threshold corresponding to the discard_percentile.
    If discard_percentile is 40, this returns the 40th percentile score.
    Videos with score < threshold are discarded.
    """
    if not scores:
        return 0.0
    
    import numpy as np
    percentile = config.filter.discard_percentile
    threshold = np.percentile(scores, percentile)
    return float(threshold)

def get_config(config_path: str = "config.yaml") -> Config:
    if os.path.exists(config_path):
        return load_config(config_path)
    return create_default_config()

def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Create a default config and save it if it doesn't exist
    default_path = Path("config.yaml")
    if not default_path.exists():
        cfg = create_default_config()
        save_config(cfg, str(default_path))
        logger.info(f"Created default config at {default_path}")
    else:
        cfg = load_config(str(default_path))
        logger.info(f"Loaded config from {default_path}")
        logger.info(f"Filter discard_percentile: {cfg.filter.discard_percentile}")

if __name__ == "__main__":
    main()