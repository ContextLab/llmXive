"""
Configuration management for the llmXive project.
Loads and validates experiment parameters from YAML.
"""
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import yaml

from .utils import setup_logging


@dataclass
class TopologyConfig:
    """Configuration for topology generation."""
    min_hinges: int = 3
    max_hinges: int = 10
    stiffness_range: tuple = field(default_factory=lambda: (0.1, 1.0))


@dataclass
class SolverConfig:
    """Configuration for the symbolic solver."""
    timeout_per_step_ms: float = 300000.0
    max_retries: int = 5
    retry_backoff_multiplier: float = 2.0
    initial_retry_delay_s: float = 1.0


@dataclass
class ExperimentConfig:
    """Configuration for the overall experiment."""
    seed: int = 42
    trial_count: int = 50
    sim_fps: int = 60
    timeout_limits: float = 3600.0  # Global timeout in seconds
    topology_counts: List[int] = field(default_factory=lambda: list(range(3, 11)))


@dataclass
class Config:
    """Master configuration container."""
    topology: TopologyConfig = field(default_factory=TopologyConfig)
    solver: SolverConfig = field(default_factory=SolverConfig)
    experiment: ExperimentConfig = field(default_factory=ExperimentConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create Config from a dictionary."""
        topology_data = data.get('topology', {})
        solver_data = data.get('solver', {})
        experiment_data = data.get('experiment', {})

        return cls(
            topology=TopologyConfig(
                min_hinges=topology_data.get('min_hinges', 3),
                max_hinges=topology_data.get('max_hinges', 10),
                stiffness_range=tuple(topology_data.get('stiffness_range', [0.1, 1.0]))
            ),
            solver=SolverConfig(
                timeout_per_step_ms=solver_data.get('timeout_per_step_ms', 300000.0),
                max_retries=solver_data.get('max_retries', 5),
                retry_backoff_multiplier=solver_data.get('retry_backoff_multiplier', 2.0),
                initial_retry_delay_s=solver_data.get('initial_retry_delay_s', 1.0)
            ),
            experiment=ExperimentConfig(
                seed=experiment_data.get('seed', 42),
                trial_count=experiment_data.get('trial_count', 50),
                sim_fps=experiment_data.get('sim_fps', 60),
                timeout_limits=experiment_data.get('timeout_limits', 3600.0),
                topology_counts=experiment_data.get('topology_counts', list(range(3, 11)))
            )
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Config to dictionary."""
        return {
            'topology': {
                'min_hinges': self.topology.min_hinges,
                'max_hinges': self.topology.max_hinges,
                'stiffness_range': list(self.topology.stiffness_range)
            },
            'solver': {
                'timeout_per_step_ms': self.solver.timeout_per_step_ms,
                'max_retries': self.solver.max_retries,
                'retry_backoff_multiplier': self.solver.retry_backoff_multiplier,
                'initial_retry_delay_s': self.solver.initial_retry_delay_s
            },
            'experiment': {
                'seed': self.experiment.seed,
                'trial_count': self.experiment.trial_count,
                'sim_fps': self.experiment.sim_fps,
                'timeout_limits': self.experiment.timeout_limits,
                'topology_counts': self.experiment.topology_counts
            }
        }


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Path to config file. If None, uses default path.

    Returns:
        Config object.
    """
    if config_path is None:
        config_path = get_default_config_path()

    logger = setup_logging()
    logger.info(f"Loading config from {config_path}")

    if not os.path.exists(config_path):
        logger.warning(f"Config file {config_path} not found. Creating default.")
        create_default_config_file(config_path)

    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)

    return Config.from_dict(data)


def save_config(config: Config, config_path: Optional[str] = None) -> None:
    """
    Save configuration to a YAML file.

    Args:
        config: Config object to save.
        config_path: Path to save to. If None, uses default path.
    """
    if config_path is None:
        config_path = get_default_config_path()

    os.makedirs(os.path.dirname(config_path) or '.', exist_ok=True)

    with open(config_path, 'w') as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False)


def create_default_config_file(config_path: Optional[str] = None) -> str:
    """
    Create a default configuration file.

    Args:
        config_path: Path to create. If None, uses default path.

    Returns:
        Path to the created file.
    """
    if config_path is None:
        config_path = get_default_config_path()

    default_config = Config()
    save_config(default_config, config_path)
    return config_path


def get_default_config_path() -> str:
    """Get the default path for the config file."""
    return os.path.join(os.path.dirname(__file__), 'config.yaml')
