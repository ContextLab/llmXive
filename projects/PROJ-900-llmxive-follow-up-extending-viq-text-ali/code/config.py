"""
Configuration Module (T004).

Defines configuration dataclasses and helper to load settings.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional
import json
import os

@dataclass
class DatasetLimits:
    max_train_samples: int = 1000
    max_val_samples: int = 200
    max_test_samples: int = 50
    # T013a/b: Dynamic batch size tuning limits
    max_batch_size: int = 32
    min_batch_size: int = 1

@dataclass
class Paths:
    data_raw: str = "data/raw"
    data_processed: str = "data/processed"
    data_results: str = "data/results"
    codebook_path: str = "data/results/codebook_v0.pth"
    embeddings_path: str = "data/results/embeddings_high_res.h5"

@dataclass
class Thresholds:
    semantic_threshold: float = 5.0  # Percentage difference threshold
    psnr_min: float = 15.0
    ssim_min: float = 0.5

@dataclass
class Config:
    batch_size: int = 8
    learning_rate: float = 1e-4
    seed: int = 42
    dataset_limits: DatasetLimits = field(default_factory=DatasetLimits)
    paths: Paths = field(default_factory=Paths)
    thresholds: Thresholds = field(default_factory=Thresholds)
    # T019: High res settings
    high_res_target: int = 1024
    low_res_target: int = 64

def get_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from a JSON file or return defaults.
    """
    config = Config()
    
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            data = json.load(f)
            # Update fields
            if 'batch_size' in data: config.batch_size = data['batch_size']
            if 'learning_rate' in data: config.learning_rate = data['learning_rate']
            if 'seed' in data: config.seed = data['seed']
            if 'high_res_target' in data: config.high_res_target = data['high_res_target']
            if 'low_res_target' in data: config.low_res_target = data['low_res_target']
            
            # Nested objects
            if 'dataset_limits' in data:
                for k, v in data['dataset_limits'].items():
                    if hasattr(config.dataset_limits, k):
                        setattr(config.dataset_limits, k, v)
            if 'paths' in data:
                for k, v in data['paths'].items():
                    if hasattr(config.paths, k):
                        setattr(config.paths, k, v)
            if 'thresholds' in data:
                for k, v in data['thresholds'].items():
                    if hasattr(config.thresholds, k):
                        setattr(config.thresholds, k, v)
    
    return config
