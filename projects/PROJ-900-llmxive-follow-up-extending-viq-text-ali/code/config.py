"""
T004: Configuration Management

Defines explicit keys for batch_size, learning_rate, seed, dataset_limits, paths, and thresholds.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional
import json
import os
import torch

@dataclass
class DatasetLimits:
    max_train_samples: int = 1000
    max_val_samples: int = 100
    max_test_samples: int = 50
    # Streaming limits
    max_streaming_batches: int = 100

@dataclass
class Paths:
    data_raw: str = "data/raw"
    data_processed: str = "data/processed"
    data_results: str = "data/results"
    checkpoints: str = "data/results/checkpoints"
    figures: str = "data/results/figures"
    logs: str = "data/results/logs"

@dataclass
class Thresholds:
    semantic_threshold: float = 0.05
    psnr_threshold: float = 25.0
    ssim_threshold: float = 0.85
    ram_limit_gb: float = 7.0

@dataclass
class Config:
    batch_size: int = 8
    learning_rate: float = 1e-4
    seed: int = 42
    device: str = "cpu" # Default to CPU as per constraints
    dataset_limits: DatasetLimits = field(default_factory=DatasetLimits)
    paths: Paths = field(default_factory=Paths)
    thresholds: Thresholds = field(default_factory=Thresholds)
    max_steps: int = 10000
    checkpoint_interval: int = 1000

    def __post_init__(self):
        if torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "batch_size": self.batch_size,
            "learning_rate": self.learning_rate,
            "seed": self.seed,
            "device": self.device,
            "dataset_limits": {
                "max_train_samples": self.dataset_limits.max_train_samples,
                "max_val_samples": self.dataset_limits.max_val_samples,
                "max_test_samples": self.dataset_limits.max_test_samples,
                "max_streaming_batches": self.dataset_limits.max_streaming_batches
            },
            "paths": {
                "data_raw": self.paths.data_raw,
                "data_processed": self.paths.data_processed,
                "data_results": self.paths.data_results,
                "checkpoints": self.paths.checkpoints,
                "figures": self.paths.figures,
                "logs": self.paths.logs
            },
            "thresholds": {
                "semantic_threshold": self.thresholds.semantic_threshold,
                "psnr_threshold": self.thresholds.psnr_threshold,
                "ssim_threshold": self.thresholds.ssim_threshold,
                "ram_limit_gb": self.thresholds.ram_limit_gb
            },
            "max_steps": self.max_steps,
            "checkpoint_interval": self.checkpoint_interval
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        config = cls()
        if "batch_size" in data: config.batch_size = data["batch_size"]
        if "learning_rate" in data: config.learning_rate = data["learning_rate"]
        if "seed" in data: config.seed = data["seed"]
        if "device" in data: config.device = data["device"]
        if "max_steps" in data: config.max_steps = data["max_steps"]
        if "checkpoint_interval" in data: config.checkpoint_interval = data["checkpoint_interval"]
        
        if "dataset_limits" in data:
            dl = data["dataset_limits"]
            config.dataset_limits = DatasetLimits(
                max_train_samples=dl.get("max_train_samples", 1000),
                max_val_samples=dl.get("max_val_samples", 100),
                max_test_samples=dl.get("max_test_samples", 50),
                max_streaming_batches=dl.get("max_streaming_batches", 100)
            )
        
        if "paths" in data:
            p = data["paths"]
            config.paths = Paths(
                data_raw=p.get("data_raw", "data/raw"),
                data_processed=p.get("data_processed", "data/processed"),
                data_results=p.get("data_results", "data/results"),
                checkpoints=p.get("checkpoints", "data/results/checkpoints"),
                figures=p.get("figures", "data/results/figures"),
                logs=p.get("logs", "data/results/logs")
            )

        if "thresholds" in data:
            t = data["thresholds"]
            config.thresholds = Thresholds(
                semantic_threshold=t.get("semantic_threshold", 0.05),
                psnr_threshold=t.get("psnr_threshold", 25.0),
                ssim_threshold=t.get("ssim_threshold", 0.85),
                ram_limit_gb=t.get("ram_limit_gb", 7.0)
            )
        return config

_config: Optional[Config] = None

def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config

def set_config(new_config: Config) -> None:
    global _config
    _config = new_config
