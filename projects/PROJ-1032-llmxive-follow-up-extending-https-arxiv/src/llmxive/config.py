"""Configuration management for llmXive."""
import os
import json
from dataclasses import dataclass, field
from typing import List, Optional, Any
from pathlib import Path

@dataclass
class ModelConfig:
    model_id: str
    max_length: int = 512
    quantization_bits: int = 8
    device: str = "cpu"

@dataclass
class TrainingConfig:
    staleness_level: int = 0
    batch_size: int = 1
    max_steps: int = 1000
    seed: int = 42
    memory_limit_gb: float = 6.5

@dataclass
class DataConfig:
    dataset_name: str = "openai/gsm8k"
    split: str = "train"
    validation_split: float = 0.1

@dataclass
class ProjectConfig:
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent)
    model_configs: List[ModelConfig] = field(default_factory=list)
    training_config: TrainingConfig = field(default_factory=TrainingConfig)
    data_config: DataConfig = field(default_factory=DataConfig)
    output_dir: Path = field(default_factory=lambda: Path("data/processed"))
    log_dir: Path = field(default_factory=lambda: Path("data/logs"))

    def __post_init__(self):
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        (self.project_root / "data" / "raw").mkdir(parents=True, exist_ok=True)
        (self.project_root / "data" / "figures").mkdir(parents=True, exist_ok=True)
        (self.project_root / "data" / "models").mkdir(parents=True, exist_ok=True)

def load_config(config_path: Optional[str] = None) -> ProjectConfig:
    """Load configuration from a JSON file or return defaults."""
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            data = json.load(f)
        # Simple mapping for demo; in real usage, nested parsing is needed
        return ProjectConfig(
            model_configs=[ModelConfig(**m) for m in data.get('models', [])],
            training_config=TrainingConfig(**data.get('training', {})),
            data_config=DataConfig(**data.get('data', {}))
        )
    return ProjectConfig()
