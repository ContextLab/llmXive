import os
from dataclasses import dataclass, field
from typing import List, Optional
import logging
import json

@dataclass
class NoiseSweepConfig:
    sigma_min: float = 0.01
    sigma_max: float = 0.20
    step: float = 0.01
    random_seed: int = 42

@dataclass
class ModelConfig:
    model_name: str = "distilbert-base-uncased"
    hidden_size: int = 768
    device: str = "cpu"
    max_length: int = 512

@dataclass
class ValidityConfig:
    input_drift_threshold: float = 0.95
    output_validity_threshold: float = 0.85
    collapse_threshold: float = 0.90

@dataclass
class MemoryConfig:
    peak_rss_limit_gb: float = 7.0
    profile_output: str = "data/processed/memory_profile.json"

@dataclass
class DataConfig:
    dataset_name: str = "bigbench_lite"
    dataset_url: str = "https://huggingface.co/datasets/google/bigbench_lite"
    cache_dir: str = "data/cache"
    pairing_config_path: str = "data/processed/pairing_config.json"

@dataclass
class OutputPaths:
    baseline_vectors: str = "data/processed/baseline_vectors.csv"
    perturbed_vectors: str = "data/processed/perturbed_vectors.csv"
    validity_log: str = "data/processed/validity_log.csv"
    statistical_results: str = "data/processed/statistical_results.json"
    trade_off_curve: str = "data/processed/trade_off_curve.csv"
    global_trade_off: str = "data/processed/global_trade_off_curve.csv"
    sensitivity_report: str = "data/processed/sensitivity_report.json"
    no_valid_sigma_report: str = "data/processed/no_valid_sigma_report.json"
    memory_profile: str = "data/processed/memory_profile.json"
    sweep_log: str = "logs/sweep.log"

@dataclass
class PipelineConfig:
    noise_config: NoiseSweepConfig = field(default_factory=NoiseSweepConfig)
    model_config: ModelConfig = field(default_factory=ModelConfig)
    validity_config: ValidityConfig = field(default_factory=ValidityConfig)
    memory_config: MemoryConfig = field(default_factory=MemoryConfig)
    data_config: DataConfig = field(default_factory=DataConfig)
    output_paths: OutputPaths = field(default_factory=OutputPaths)
    dry_run: bool = False

def load_config(config_path: Optional[str] = None) -> PipelineConfig:
    """Load configuration from a JSON file or return defaults."""
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            data = json.load(f)
        # Map JSON keys to dataclass fields (simplified)
        # In a real scenario, use a proper deserialization library
        return PipelineConfig(
            noise_config=NoiseSweepConfig(**data.get('noise_config', {})),
            model_config=ModelConfig(**data.get('model_config', {})),
            validity_config=ValidityConfig(**data.get('validity_config', {})),
            memory_config=MemoryConfig(**data.get('memory_config', {})),
            data_config=DataConfig(**data.get('data_config', {})),
            output_paths=OutputPaths(**data.get('output_paths', {})),
            dry_run=data.get('dry_run', False)
        )
    return PipelineConfig()
