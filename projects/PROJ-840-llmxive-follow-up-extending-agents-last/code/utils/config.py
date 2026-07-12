"""
Configuration Loader Module.

Handles loading of model paths, checkpoint intervals, and normalization constants
from the YAML schema defined in config_schema.yaml.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
import logging

@dataclass
class ModelConfig:
    path: str
    max_tokens: int
    temperature: float
    top_p: float

@dataclass
class CheckpointConfig:
    interval_n: int
    memory_limit_mb: int
    timeout_hours: int

@dataclass
class LoggingConfig:
    level: str
    format: str
    file: str

@dataclass
class DataPathsConfig:
    raw_dir: str
    processed_dir: str
    figures_dir: str
    golden_subset: str
    baseline_results: str
    intervention_results: str

@dataclass
class NormalizationConfig:
    float_tolerance: float
    timestamp_placeholder: str
    id_placeholder: str
    ref_placeholder: str
    timestamp_regex: str
    uuid_regex: str
    reference_regex: str

@dataclass
class StatsConfig:
    significance_level: float
    correction_method: str
    sensitivity_intervals: list

@dataclass
class PipelineConfig:
    name: str
    version: str
    model: ModelConfig
    checkpoint: CheckpointConfig
    logging: LoggingConfig
    data_paths: DataPathsConfig
    normalization: NormalizationConfig
    stats: StatsConfig

@dataclass
class PipelineConfigWrapper:
    config: PipelineConfig
    raw_config: Dict[str, Any]

def load_config(config_path: Optional[str] = None) -> PipelineConfigWrapper:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config file. If None, defaults to 
                   code/utils/config_schema.yaml
                   
    Returns:
        PipelineConfigWrapper containing parsed configuration
        
    Raises:
        FileNotFoundError: If config file does not exist
        yaml.YAMLError: If YAML is invalid
    """
    if config_path is None:
        config_path = Path(__file__).parent / "config_schema.yaml"
    
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        raw_data = yaml.safe_load(f)
    
    # Parse nested configurations
    model_cfg = ModelConfig(
        path=raw_data['model']['path'],
        max_tokens=raw_data['model']['max_tokens'],
        temperature=raw_data['model']['temperature'],
        top_p=raw_data['model']['top_p']
    )
    
    checkpoint_cfg = CheckpointConfig(
        interval_n=raw_data['checkpoint']['interval_n'],
        memory_limit_mb=raw_data['checkpoint']['memory_limit_mb'],
        timeout_hours=raw_data['checkpoint']['timeout_hours']
    )
    
    logging_cfg = LoggingConfig(
        level=raw_data['logging']['level'],
        format=raw_data['logging']['format'],
        file=raw_data['logging']['file']
    )
    
    paths_cfg = DataPathsConfig(
        raw_dir=raw_data['data_paths']['raw_dir'],
        processed_dir=raw_data['data_paths']['processed_dir'],
        figures_dir=raw_data['data_paths']['figures_dir'],
        golden_subset=raw_data['data_paths']['golden_subset'],
        baseline_results=raw_data['data_paths']['baseline_results'],
        intervention_results=raw_data['data_paths']['intervention_results']
    )
    
    norm_cfg_data = raw_data['normalization']
    norm_cfg = NormalizationConfig(
        float_tolerance=float(norm_cfg_data['float_tolerance']),
        timestamp_placeholder=norm_cfg_data['timestamp_placeholder'],
        id_placeholder=norm_cfg_data['id_placeholder'],
        ref_placeholder=norm_cfg_data['ref_placeholder'],
        timestamp_regex=norm_cfg_data['timestamp_regex'],
        uuid_regex=norm_cfg_data['uuid_regex'],
        reference_regex=norm_cfg_data['reference_regex']
    )
    
    stats_cfg_data = raw_data['stats']
    stats_cfg = StatsConfig(
        significance_level=float(stats_cfg_data['significance_level']),
        correction_method=stats_cfg_data['correction_method'],
        sensitivity_intervals=stats_cfg_data['sensitivity_intervals']
    )
    
    pipeline_cfg = PipelineConfig(
        name=raw_data['pipeline']['name'],
        version=raw_data['pipeline']['version'],
        model=model_cfg,
        checkpoint=checkpoint_cfg,
        logging=logging_cfg,
        data_paths=paths_cfg,
        normalization=norm_cfg,
        stats=stats_cfg
    )
    
    return PipelineConfigWrapper(config=pipeline_cfg, raw_config=raw_data)

def validate_config(wrapper: PipelineConfigWrapper) -> bool:
    """
    Validate loaded configuration against expected types and ranges.
    
    Returns:
        True if valid, False otherwise
    """
    cfg = wrapper.config
    
    # Validate model
    if not cfg.model.path:
        return False
    if cfg.model.max_tokens <= 0:
        return False
    if not 0.0 <= cfg.model.temperature <= 2.0:
        return False
        
    # Validate checkpoint
    if cfg.checkpoint.interval_n <= 0:
        return False
    if cfg.checkpoint.memory_limit_mb <= 0:
        return False
        
    # Validate normalization
    if cfg.normalization.float_tolerance <= 0:
        return False
        
    return True

def main():
    """CLI entry point to load and print config."""
    try:
        wrapper = load_config()
        if validate_config(wrapper):
            print("Configuration loaded and validated successfully.")
            print(f"Pipeline: {wrapper.config.name} v{wrapper.config.version}")
            print(f"Model: {wrapper.config.model.path}")
            print(f"Checkpoint interval: {wrapper.config.checkpoint.interval_n}")
            print(f"Float tolerance: {wrapper.config.normalization.float_tolerance}")
        else:
            print("Configuration validation failed.")
            exit(1)
    except Exception as e:
        print(f"Error loading config: {e}")
        exit(1)

if __name__ == "__main__":
    main()
