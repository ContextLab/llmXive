"""
config.py

Defines configuration dataclasses and loading logic for the pipeline.
"""

import os
import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)

@dataclass
class NoiseSweepConfig:
    sigma_min: float = 0.01
    sigma_max: float = 0.20
    step: float = 0.01
    seeds: List[int] = field(default_factory=lambda: [42])

@dataclass
class ModelConfig:
    model_name: str = "distilbert-base-uncased"
    hidden_size: int = 768
    device: str = "cpu"
    max_length: int = 512

@dataclass
class ValidityConfig:
    input_drift_threshold: float = 0.95
    output_validity_bert_score: float = 0.85
    output_validity_perplexity_bound: float = 2.0
    collapse_threshold: float = 0.90
    no_valid_sigma_threshold: float = 0.10  # T051: Threshold for inconclusive report

@dataclass
class MemoryConfig:
    peak_rss_limit_gb: float = 7.0
    log_interval_mb: int = 100

@dataclass
class DataConfig:
    dataset_name: str = "bigbench_lite"
    dataset_url: str = "https://huggingface.co/datasets/google/bigbench_lite"
    expected_hash: str = ""  # To be populated from checksums.json or config
    expected_answer_col: str = "expected_answer"

@dataclass
class OutputPaths:
    data_raw: str = "data/raw"
    data_processed: str = "data/processed"
    logs: str = "logs"
    figures: str = "figures"
    
    # Specific output files
    baseline_vectors: str = "data/processed/baseline_vectors.csv"
    perturbed_vectors: str = "data/processed/perturbed_vectors.csv"
    validity_log: str = "data/processed/validity_log.csv"
    statistical_results: str = "data/processed/statistical_results.json"
    memory_profile: str = "data/processed/memory_profile.json"
    inconclusive_report: str = "data/processed/inconclusive_report.md" # T051
    filtered_pairs_input_drift: str = "data/processed/filtered_pairs_input_drift.csv"
    filtered_pairs_output_validity: str = "data/processed/filtered_pairs_output_validity.csv"
    filtered_pairs_analysis: str = "data/processed/filtered_pairs_for_analysis.csv"
    trade_off_curve: str = "data/processed/trade_off_curve.csv"
    global_trade_off_curve: str = "data/processed/global_trade_off_curve.csv"
    sensitivity_report: str = "data/processed/sensitivity_report.json"
    pairing_config: str = "data/processed/pairing_config.json"
    checksums: str = "data/checksums.json"

@dataclass
class PipelineConfig:
    noise_sweep: NoiseSweepConfig = field(default_factory=NoiseSweepConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    validity: ValidityConfig = field(default_factory=ValidityConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    data: DataConfig = field(default_factory=DataConfig)
    output: OutputPaths = field(default_factory=OutputPaths)
    # T051: Ensure data_config is accessible if referenced elsewhere
    data_config: DataConfig = field(default_factory=DataConfig) 

def load_config(config_path: Optional[str] = None) -> PipelineConfig:
    """
    Loads configuration from a JSON file or returns defaults.
    """
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        # Map JSON keys to dataclass fields (simplified mapping)
        noise = data.get('noise_sweep', {})
        model = data.get('model', {})
        validity = data.get('validity', {})
        memory = data.get('memory', {})
        data_cfg = data.get('data', {})
        output = data.get('output', {})

        return PipelineConfig(
            noise_sweep=NoiseSweepConfig(**noise),
            model=ModelConfig(**model),
            validity=ValidityConfig(**validity),
            memory=MemoryConfig(**memory),
            data=DataConfig(**data_cfg),
            output=OutputPaths(**output),
            data_config=DataConfig(**data_cfg) # Explicit assignment for T051 fix
        )
    else:
        logger.info("No config file found. Using defaults.")
        return PipelineConfig()

if __name__ == "__main__":
    # Test loading
    cfg = load_config()
    print(f"Config loaded: {cfg}")
