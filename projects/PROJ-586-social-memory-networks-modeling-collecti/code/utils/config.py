"""Configuration management for the social memory networks project."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

@dataclass
class ExperimentConfig:
    """Core experiment configuration."""
    seed: int = 42
    device: str = "cpu"
    model_name: str = "facebook/opt-125m"
    context: str = "full"  # 'full' or 'limited'
    num_agents: int = 5
    dataset: str = "hanabi"
    games: int = 1000
    output_dir: str = "projects/PROJ-586-social-memory-networks-modeling-collecti/results"
    token_limit: Optional[int] = None  # For limited context

def load_config(config_path: Optional[Path] = None) -> ExperimentConfig:
    """Load configuration from a JSON file if provided, otherwise return defaults."""
    if config_path and config_path.exists():
        with open(config_path, 'r') as f:
            data = json.load(f)
        return ExperimentConfig(**data)
    return ExperimentConfig()

def save_config(config: ExperimentConfig, config_path: Path) -> None:
    """Save configuration to a JSON file."""
    with open(config_path, 'w') as f:
        json.dump({
            'seed': config.seed,
            'device': config.device,
            'model_name': config.model_name,
            'context': config.context,
            'num_agents': config.num_agents,
            'dataset': config.dataset,
            'games': config.games,
            'output_dir': config.output_dir,
            'token_limit': config.token_limit
        }, f, indent=2)
