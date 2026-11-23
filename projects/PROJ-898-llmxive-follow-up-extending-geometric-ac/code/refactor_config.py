"""
Refactored configuration management for llmXive.
Provides typed configuration classes and YAML loading/saving.
"""
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)

@dataclass
class TopologyConfig:
    """Configuration for topology generation."""
    count_range: List[int] = field(default_factory=lambda: [3, 10])
    max_attempts: int = 1000
    target_count: int = 50

@dataclass
class SolverConfig:
    """Configuration for the symbolic solver."""
    timeout_limits: float = 300.0
    stiffness_range: List[float] = field(default_factory=lambda: [0.1, 0.5])
    max_iterations: int = 100

@dataclass
class ExperimentConfig:
    """Configuration for experiment parameters."""
    seed: int = 42
    trial_count: int = 50
    sim_fps: int = 240
    target_zone: Dict[str, Any] = field(
        default_factory=lambda: {"center": [0.0, 0.0, 0.0], "radius": 0.1}
    )

@dataclass
class Config:
    """Main configuration container."""
    topology: TopologyConfig = field(default_factory=TopologyConfig)
    solver: SolverConfig = field(default_factory=SolverConfig)
    experiment: ExperimentConfig = field(default_factory=ExperimentConfig)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "topology": {
                "count_range": self.topology.count_range,
                "max_attempts": self.topology.max_attempts,
                "target_count": self.topology.target_count,
            },
            "solver": {
                "timeout_limits": self.solver.timeout_limits,
                "stiffness_range": self.solver.stiffness_range,
                "max_iterations": self.solver.max_iterations,
            },
            "experiment": {
                "seed": self.experiment.seed,
                "trial_count": self.experiment.trial_count,
                "sim_fps": self.experiment.sim_fps,
                "target_zone": self.experiment.target_zone,
            },
        }

def load_config(config_path: str) -> Config:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Config object populated with values from the file.

    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the file contains invalid YAML.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        data = yaml.safe_load(f)

    config = Config()

    if "topology" in data:
        topo_data = data["topology"]
        config.topology = TopologyConfig(
            count_range=topo_data.get("count_range", config.topology.count_range),
            max_attempts=topo_data.get("max_attempts", config.topology.max_attempts),
            target_count=topo_data.get("target_count", config.topology.target_count),
        )

    if "solver" in data:
        solver_data = data["solver"]
        config.solver = SolverConfig(
            timeout_limits=solver_data.get("timeout_limits", config.solver.timeout_limits),
            stiffness_range=solver_data.get("stiffness_range", config.solver.stiffness_range),
            max_iterations=solver_data.get("max_iterations", config.solver.max_iterations),
        )

    if "experiment" in data:
        exp_data = data["experiment"]
        config.experiment = ExperimentConfig(
            seed=exp_data.get("seed", config.experiment.seed),
            trial_count=exp_data.get("trial_count", config.experiment.trial_count),
            sim_fps=exp_data.get("sim_fps", config.experiment.sim_fps),
            target_zone=exp_data.get("target_zone", config.experiment.target_zone),
        )

    return config

def save_config(config: Config, config_path: str) -> None:
    """
    Save configuration to a YAML file.

    Args:
        config: Config object to save.
        config_path: Path to the output YAML file.
    """
    os.makedirs(os.path.dirname(config_path) or ".", exist_ok=True)
    with open(config_path, "w") as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False)

def create_default_config_file(config_path: Optional[str] = None) -> str:
    """
    Create a default configuration file.

    Args:
        config_path: Optional path for the default config. If None, uses default path.

    Returns:
        Path to the created configuration file.
    """
    if config_path is None:
        config_path = get_default_config_path()

    default_config = Config()
    save_config(default_config, config_path)
    logger.info(f"Created default config at {config_path}")
    return config_path

def get_default_config_path() -> str:
    """
    Get the default path for the configuration file.

    Returns:
        Default config file path.
    """
    return os.path.join("code", "config.yaml")
