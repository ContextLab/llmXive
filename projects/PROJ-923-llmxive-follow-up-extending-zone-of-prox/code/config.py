import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

# Default configuration file path relative to project root
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"

class Config:
    """
    Central configuration loader for the llmXive Follow-up project.
    Loads settings from config.yaml and exposes them as typed properties.
    """

    def __init__(self, data: Dict[str, Any]):
        self.data = data
        # Top-level sections
        self.project = data.get("project", {})
        self.paths = data.get("paths", {})
        self.simulation = data.get("simulation", {})
        self.mmlu = data.get("mmlu", {})
        self.logging = data.get("logging", {})
        self.caps = data.get("caps", {})  # Confidence Adaptive Pruning specific settings

    @property
    def seed(self) -> int:
        """Global random seed for reproducibility."""
        return self.project.get("seed", 42)

    @property
    def data_dir(self) -> Path:
        """Base directory for all data artifacts."""
        return Path(self.paths.get("data_dir", "data")).resolve()

    @property
    def output_dir(self) -> Path:
        """Directory for metric outputs (CSV, reports)."""
        return Path(self.paths.get("output_dir", "data/metrics")).resolve()

    @property
    def figures_dir(self) -> Path:
        """Directory for generated plots."""
        return Path(self.paths.get("figures_dir", "data/figures")).resolve()

    @property
    def state_dir(self) -> Path:
        """Directory for persistent state (e.g., history logs)."""
        return Path(self.paths.get("state_dir", "state")).resolve()

    @property
    def contracts_dir(self) -> Path:
        """Directory containing schema contracts."""
        return Path(self.paths.get("contracts_dir", "contracts")).resolve()

    @property
    def buffer_cycles(self) -> int:
        """Number of training cycles per simulation run."""
        return self.simulation.get("buffer_cycles", 100)

    @property
    def noise_sigma(self) -> float:
        """Standard deviation for Gaussian noise injection in confidence scores."""
        return self.simulation.get("noise_sigma", 0.05)

    @property
    def mmlu_subset(self) -> str:
        """Specific MMLU subset to use (e.g., 'high_school_mathematics')."""
        return self.mmlu.get("subset", "high_school_mathematics")

    @property
    def mmlu_held_out_subset(self) -> str:
        """MMLU subset for held-out test evaluation."""
        return self.mmlu.get("held_out_subset", "high_school_computer_science")

    # CAP Specific Thresholds
    @property
    def cap_rejected_threshold(self) -> float:
        """Lower confidence threshold for 'consistently rejected' classification."""
        return self.caps.get("rejected_threshold", 0.1)

    @property
    def cap_accepted_threshold(self) -> float:
        """Upper confidence threshold for 'consistently accepted' classification."""
        return self.caps.get("accepted_threshold", 0.9)

    @property
    def cap_min_candidates(self) -> int:
        """Minimum number of candidates to keep in NCQ prompt even if all are pruned."""
        return self.caps.get("min_candidates", 1)

    @property
    def log_level(self) -> int:
        """Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)."""
        level_str = self.logging.get("level", "INFO").upper()
        return getattr(logging, level_str, logging.INFO)

import logging

_config: Optional[Config] = None

def get_config() -> Config:
    """
    Returns the singleton Config instance, loading from disk if necessary.
    """
    global _config
    if _config is None:
        _config = reload_config()
    return _config

def reload_config() -> Config:
    """
    Forces a reload of the configuration from disk.
    Raises FileNotFoundError if config.yaml is missing.
    """
    global _config
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Configuration file not found at {CONFIG_PATH}. "
            "Please ensure config.yaml exists in the project root."
        )
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    _config = Config(data)
    return _config
