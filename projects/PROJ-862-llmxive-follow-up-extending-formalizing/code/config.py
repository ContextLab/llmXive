import os
from dataclasses import dataclass, field
from typing import List, Optional
import logging
import json

logger = logging.getLogger(__name__)

@dataclass
class NoiseSweepConfig:
    sigma_low: float = 0.1
    sigma_high: float = 2.0
    sigma_steps: int = 10
    task_types: List[str] = field(default_factory=list)

@dataclass
class ModelConfig:
    model_name: str = "google-bert/bert-base-uncased"
    tokenizer_name: str = "google-bert/bert-base-uncased"
    hidden_size: int = 768
    device: str = "cpu"
    max_length: int = 512

@dataclass
class ValidityConfig:
    f1_threshold: float = 0.85
    perplexity_multiplier: float = 2.0
    input_drift_threshold: float = 0.95

@dataclass
class MemoryConfig:
    peak_rss_limit_gb: float = 7.0
    check_interval_seconds: float = 1.0

@dataclass
class DataConfig:
    dataset_name: str = "big_bench_reasoning"
    split: str = "train"
    streaming: bool = True
    batch_size: int = 32

@dataclass
class OutputPaths:
    base_dir: str = "data/processed"
    baseline_vectors: str = "baseline_vectors.csv"
    perturbed_vectors: str = "perturbed_vectors.csv"
    validity_log: str = "validity_log.csv"
    sensitivity_report: str = "sensitivity_report.json"
    statistical_results: str = "statistical_results.json"
    pairing_config: str = "pairing_config.json"

@dataclass
class PipelineConfig:
    noise: NoiseSweepConfig = field(default_factory=NoiseSweepConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    validity: ValidityConfig = field(default_factory=ValidityConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    data: DataConfig = field(default_factory=DataConfig)
    output: OutputPaths = field(default_factory=OutputPaths)
    seed: int = 42

def load_config(config_path: Optional[str] = None) -> PipelineConfig:
    """
    Loads configuration from a JSON file or returns defaults.
    """
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            data = json.load(f)
        # Map JSON keys to dataclass fields
        # This is a simplified loader; in production, use a library like pydantic
        return PipelineConfig(
            noise=NoiseSweepConfig(**data.get('noise', {})),
            model=ModelConfig(**data.get('model', {})),
            validity=ValidityConfig(**data.get('validity', {})),
            memory=MemoryConfig(**data.get('memory', {})),
            data=DataConfig(**data.get('data', {})),
            output=OutputPaths(**data.get('output', {})),
            seed=data.get('seed', 42)
        )
    return PipelineConfig()
