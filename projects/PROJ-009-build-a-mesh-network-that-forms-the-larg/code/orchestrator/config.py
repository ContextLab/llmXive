"""
Configuration management for the mesh network orchestrator.

Loads YAML configuration files and provides a global random_seed
(Principle I: Reproducibility) that is mirrored in sweep_config.yaml
and used by all stochastic components.
"""
from __future__ import annotations

import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

@dataclass
class GranularityConfig:
    fine: int = 1
    medium: int = 2
    coarse: int = 3

@dataclass
class NetworkConfig:
    base_latency_ms: int = 10
    packet_loss_rate: float = 0.0
    bandwidth_mbps: float = 100.0
    snr_db: float = 30.0

@dataclass
class Config:
    testbed: Dict[str, Any] = field(default_factory=dict)
    benchmark: Dict[str, Any] = field(default_factory=dict)
    analysis: Dict[str, Any] = field(default_factory=dict)
    ci_timeout_seconds: int = 21600  # default CI wall‑clock limit (seconds)
    random_seed: int = 42  # Global reproducibility seed (Principle I)

class ConfigError(Exception):
    """Raised when configuration loading or validation fails."""
    pass

class ConfigManager:
    """High‑level manager that loads, validates and provides access to the config."""

    def __init__(self, config_path: str):
        self.path = Path(config_path)
        self.config: Optional[Config] = None
        self._load()

    def _load(self) -> None:
        if not self.path.is_file():
            raise ConfigError(f"Config file not found: {self.path}")
        with self.path.open("rt") as f:
            raw = yaml.safe_load(f)
        if raw is None:
            raw = {}
        self.config = Config(
            testbed=raw.get("testbed", {}),
            benchmark=raw.get("benchmark", {}),
            analysis=raw.get("analysis", {}),
            ci_timeout_seconds=raw.get("ci_timeout_seconds", 21600),
            random_seed=raw.get("random_seed", 42)
        )

    def get(self) -> Config:
        if self.config is None:
            raise ConfigError("Configuration not loaded")
        return self.config

def load_config(config_path: str) -> ConfigManager:
    """Convenient helper used by the CLI and other modules."""
    return ConfigManager(config_path)

def get_config() -> Config:
    """Global accessor – loads ``config.yaml`` from the project root."""
    default_path = Path("config.yaml")
    if not default_path.is_file():
        raise ConfigError("Default config.yaml not found")
    manager = ConfigManager(str(default_path))
    return manager.get()

def save_config(config: Config, path: Optional[Path] = None) -> None:
    """Write a ``Config`` instance back to YAML."""
    target = path or Path("config.yaml")
    data = {
        "testbed": config.testbed,
        "benchmark": config.benchmark,
        "analysis": config.analysis,
        "ci_timeout_seconds": config.ci_timeout_seconds,
        "random_seed": config.random_seed,
    }
    with target.open("wt") as f:
        yaml.safe_dump(data, f)

# Compatibility alias required by contract tests
OrchestratorConfig = Config