from dataclasses import dataclass
from typing import Optional
import os

@dataclass
class Config:
    """Configuration for the distillation pipeline."""
    seed: int = 42
    max_ram_gb: float = 7.0
    max_runtime_hours: float = 6.0
    batch_size: int = 32
    learning_rate: float = 1e-4
    max_epochs: int = 100
    loss_threshold: float = 0.1
    early_stopping_patience: int = 10

def get_config() -> Config:
    """Get configuration from environment or defaults."""
    return Config(
        seed=int(os.getenv("SEED", 42)),
        max_ram_gb=float(os.getenv("MAX_RAM_GB", 7.0)),
        max_runtime_hours=float(os.getenv("MAX_RUNTIME_HOURS", 6.0))
    )
