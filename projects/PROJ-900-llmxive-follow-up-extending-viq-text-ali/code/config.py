from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional

@dataclass
class DatasetLimits:
    max_train_samples: int = 1000
    max_val_samples: int = 100
    resolution: int = 64

@dataclass
class Paths:
    data_raw: Path = field(default_factory=lambda: Path("data/raw"))
    data_processed: Path = field(default_factory=lambda: Path("data/processed"))
    data_results: Path = field(default_factory=lambda: Path("data/results"))
    code: Path = field(default_factory=lambda: Path("code"))

@dataclass
class Thresholds:
    semantic_threshold: float = 5.0  # Percentage difference threshold
    psnr_threshold: float = 15.0

@dataclass
class Config:
    batch_size: int = 8
    learning_rate: float = 1e-4
    seed: int = 42
    dataset_limits: DatasetLimits = field(default_factory=DatasetLimits)
    paths: Paths = field(default_factory=Paths)
    thresholds: Thresholds = field(default_factory=Thresholds)
    max_epochs: int = 10
    # Additional config for T016 logging
    log_level: str = "INFO"
    log_file: str = "data/results/training.log"

def get_config() -> Config:
    return Config()
