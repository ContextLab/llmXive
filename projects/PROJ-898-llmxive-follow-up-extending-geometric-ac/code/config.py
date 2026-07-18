"""
Configuration management for llmXive Geometric Action Model experiments.

Provides dataclasses and utilities for loading, saving, and validating
experiment parameters including topology counts, timeout limits, and
simulation settings.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from utils import setup_logging

# Configure module logger
logger = setup_logging(__name__)


@dataclass
class TopologyConfig:
    """Configuration for kinematic chain topologies to generate."""
    min_hinge_count: int = 2
    max_hinge_count: int = 10
    num_variations: int = 50
    include_deformable: bool = True
    deformable_types: List[str] = field(default_factory=lambda: ["soft_rope", "cloth"])
    deformable_count: int = 20
    
    def __post_init__(self):
        if self.min_hinge_count < 1:
            raise ValueError("min_hinge_count must be at least 1")
        if self.max_hinge_count < self.min_hinge_count:
            raise ValueError("max_hinge_count must be >= min_hinge_count")
        if self.num_variations < 1:
            raise ValueError("num_variations must be at least 1")
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "min_hinge_count": self.min_hinge_count,
            "max_hinge_count": self.max_hinge_count,
            "num_variations": self.num_variations,
            "include_deformable": self.include_deformable,
            "deformable_types": self.deformable_types,
            "deformable_count": self.deformable_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TopologyConfig":
        """Create instance from dictionary."""
        return cls(
            min_hinge_count=data.get("min_hinge_count", 2),
            max_hinge_count=data.get("max_hinge_count", 10),
            num_variations=data.get("num_variations", 50),
            include_deformable=data.get("include_deformable", True),
            deformable_types=data.get("deformable_types", ["soft_rope", "cloth"]),
            deformable_count=data.get("deformable_count", 20),
        )


@dataclass
class SolverConfig:
    """Configuration for symbolic solver execution."""
    timeout_seconds: float = 300.0
    max_iterations: int = 1000
    tolerance: float = 1e-6
    enable_parallel: bool = False
    num_workers: int = 2
    
    def __post_init__(self):
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.max_iterations < 1:
            raise ValueError("max_iterations must be at least 1")
        if self.tolerance <= 0:
            raise ValueError("tolerance must be positive")
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timeout_seconds": self.timeout_seconds,
            "max_iterations": self.max_iterations,
            "tolerance": self.tolerance,
            "enable_parallel": self.enable_parallel,
            "num_workers": self.num_workers,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SolverConfig":
        """Create instance from dictionary."""
        return cls(
            timeout_seconds=data.get("timeout_seconds", 300.0),
            max_iterations=data.get("max_iterations", 1000),
            tolerance=data.get("tolerance", 1e-6),
            enable_parallel=data.get("enable_parallel", False),
            num_workers=data.get("num_workers", 2),
        )


@dataclass
class ExperimentConfig:
    """
    Base configuration for experiment parameters.
    
    Contains all experiment settings including topology generation,
    solver parameters, simulation settings, and output paths.
    """
    # Experiment identification
    experiment_name: str = "llmxive_gam_follow_up"
    seed: int = 42
    output_dir: str = "data/generated"
    results_dir: str = "data/results"
    
    # Configuration sections
    topology: TopologyConfig = field(default_factory=TopologyConfig)
    solver: SolverConfig = field(default_factory=SolverConfig)
    
    # Simulation settings
    physics_dt: float = 1.0 / 240.0
    physics_steps_per_action: int = 10
    gravity: float = -9.81
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    def __post_init__(self):
        # Validate directories exist or can be created
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert entire config to dictionary."""
        return {
            "experiment_name": self.experiment_name,
            "seed": self.seed,
            "output_dir": self.output_dir,
            "results_dir": self.results_dir,
            "topology": self.topology.to_dict(),
            "solver": self.solver.to_dict(),
            "physics_dt": self.physics_dt,
            "physics_steps_per_action": self.physics_steps_per_action,
            "gravity": self.gravity,
            "log_level": self.log_level,
            "log_file": self.log_file,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExperimentConfig":
        """Create instance from dictionary."""
        topology_data = data.get("topology", {})
        solver_data = data.get("solver", {})
        
        return cls(
            experiment_name=data.get("experiment_name", "llmxive_gam_follow_up"),
            seed=data.get("seed", 42),
            output_dir=data.get("output_dir", "data/generated"),
            results_dir=data.get("results_dir", "data/results"),
            topology=TopologyConfig.from_dict(topology_data),
            solver=SolverConfig.from_dict(solver_data),
            physics_dt=data.get("physics_dt", 1.0 / 240.0),
            physics_steps_per_action=data.get("physics_steps_per_action", 10),
            gravity=data.get("gravity", -9.81),
            log_level=data.get("log_level", "INFO"),
            log_file=data.get("log_file"),
        )
    
    @classmethod
    def create_default(cls) -> "ExperimentConfig":
        """Create a configuration with default values."""
        return cls()

def load_config(config_path: str) -> ExperimentConfig:
    """
    Load experiment configuration from a JSON file.
    
    Args:
        config_path: Path to the JSON configuration file.
        
    Returns:
        ExperimentConfig instance populated with values from the file.
        
    Raises:
        FileNotFoundError: If the config file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
        ValueError: If the configuration values are invalid.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    logger.info(f"Loading configuration from: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    config = ExperimentConfig.from_dict(data)
    logger.info(f"Loaded configuration: {config.experiment_name}")
    logger.info(f"  Topology: {config.topology.num_variations} variations, "
               f"hinges {config.topology.min_hinge_count}-{config.topology.max_hinge_count}")
    logger.info(f"  Solver timeout: {config.solver.timeout_seconds}s")
    
    return config

def save_config(config: ExperimentConfig, config_path: str) -> None:
    """
    Save experiment configuration to a JSON file.
    
    Args:
        config: ExperimentConfig instance to save.
        config_path: Path to the output JSON file.
    """
    # Ensure parent directory exists
    parent_dir = os.path.dirname(config_path)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)
    
    logger.info(f"Saving configuration to: {config_path}")
    
    data = config.to_dict()
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    logger.info("Configuration saved successfully")

def create_default_config_file(output_path: str = "config/default_experiment.json") -> ExperimentConfig:
    """
    Create a default configuration file and return the config object.
    
    Args:
        output_path: Path where the JSON file will be written.
        
    Returns:
        The created ExperimentConfig instance.
    """
    config = ExperimentConfig.create_default()
    save_config(config, output_path)
    logger.info(f"Default configuration created at: {output_path}")
    return config

def get_default_config_path() -> str:
    """Return the default path for the experiment configuration file."""
    return "config/default_experiment.json"

if __name__ == "__main__":
    # Example usage: create a default config file
    config = create_default_config_file()
    print(f"Created default config: {config.to_dict()}")