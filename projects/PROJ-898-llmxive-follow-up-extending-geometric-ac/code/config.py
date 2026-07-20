"""
Configuration management for llmXive experiments.
Defines typed configuration objects and YAML loading utilities.
"""
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from .utils import setup_logging

@dataclass
class TopologyConfig:
    """Configuration for topology generation parameters."""
    min_hinge_count: int = 3
    max_hinge_count: int = 10
    object_types: List[str] = field(default_factory=lambda: ["rigid", "deformable"])
    deformable_stiffness_range: tuple = (0.1, 1.0)
    
@dataclass
class SolverConfig:
    """Configuration for symbolic solver parameters."""
    timeout_seconds: float = 300.0
    max_iterations: int = 1000
    constraint_tolerance: float = 1e-6
    
@dataclass
class ExperimentConfig:
    """Configuration for experiment execution parameters."""
    seed: int = 42
    trial_count: int = 50
    topology_counts: Dict[str, int] = field(default_factory=lambda: {"hinge_3": 10, "hinge_5": 10, "hinge_7": 10, "hinge_10": 10})
    timeout_limits: Dict[str, float] = field(default_factory=lambda: {"step": 300.0})
    
class Config:
    """Container for all configuration sections."""
    def __init__(self, topology: TopologyConfig, solver: SolverConfig, experiment: ExperimentConfig):
        self.topology = topology
        self.solver = solver
        self.experiment = experiment

def load_config(config_path: str) -> Config:
    """
    Load configuration from a YAML or JSON file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Config object with loaded parameters
    """
    logger = setup_logging()
    logger.info(f"Loading configuration from {config_path}")
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
    with open(config_path, 'r') as f:
        if config_path.endswith('.yaml') or config_path.endswith('.yml'):
            try:
                import yaml
                config_data = yaml.safe_load(f)
            except ImportError:
                raise ImportError("PyYAML is required to load YAML config files. Install with: pip install pyyaml")
        else:
            config_data = json.load(f)
    
    # Extract sections with defaults
    topology_data = config_data.get('topology', {})
    solver_data = config_data.get('solver', {})
    experiment_data = config_data.get('experiment', {})
    
    topology = TopologyConfig(**topology_data)
    solver = SolverConfig(**solver_data)
    experiment = ExperimentConfig(**experiment_data)
    
    return Config(topology, solver, experiment)

def save_config(config: Config, config_path: str) -> None:
    """
    Save configuration to a JSON file.
    
    Args:
        config: Config object to save
        config_path: Path to save configuration file
    """
    logger = setup_logging()
    logger.info(f"Saving configuration to {config_path}")
    
    config_dict = {
        'topology': {
            'min_hinge_count': config.topology.min_hinge_count,
            'max_hinge_count': config.topology.max_hinge_count,
            'object_types': config.topology.object_types,
            'deformable_stiffness_range': config.topology.deformable_stiffness_range
        },
        'solver': {
            'timeout_seconds': config.solver.timeout_seconds,
            'max_iterations': config.solver.max_iterations,
            'constraint_tolerance': config.solver.constraint_tolerance
        },
        'experiment': {
            'seed': config.experiment.seed,
            'trial_count': config.experiment.trial_count,
            'topology_counts': config.experiment.topology_counts,
            'timeout_limits': config.experiment.timeout_limits
        }
    }
    
    os.makedirs(os.path.dirname(config_path) if os.path.dirname(config_path) else '.', exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(config_dict, f, indent=2)

def create_default_config_file(output_path: Optional[str] = None) -> str:
    """
    Create a default configuration file with standard parameters.
    
    Args:
        output_path: Optional path to save the config. Defaults to 'code/config.yaml'
        
    Returns:
        Path to the created configuration file
    """
    if output_path is None:
        output_path = "code/config.yaml"
        
    default_config = Config(
        topology=TopologyConfig(),
        solver=SolverConfig(),
        experiment=ExperimentConfig()
    )
    
    save_config(default_config, output_path)
    return output_path

def get_default_config_path() -> str:
    """
    Get the default path for the configuration file.
    
    Returns:
        Default configuration file path
    """
    return "code/config.yaml"
