"""
Configuration management for the Co-Evolving Policy Distillation pipeline.

Handles seeding, generation counts, rule evaluation budgets, and file paths.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import random
import hashlib


class ConfigError(Exception):
    """Raised when configuration loading or validation fails."""
    pass


class Config:
    """
    Immutable configuration container for the research pipeline.
    
    Attributes:
        seed: Global random seed for reproducibility.
        num_generations: Number of generations for training loops.
        rule_eval_budget: Maximum number of rule evaluations allowed per run.
        data_dir: Path to the data directory.
        results_dir: Path to store results and artifacts.
        logic_config: Dict containing logic generation parameters.
        grid_config: Dict containing grid generation parameters.
        agent_config: Dict containing agent training parameters.
    """
    def __init__(
        self,
        seed: int,
        num_generations: int,
        rule_eval_budget: int,
        data_dir: str = "data",
        results_dir: str = "data/results",
        logic_config: Optional[Dict[str, Any]] = None,
        grid_config: Optional[Dict[str, Any]] = None,
        agent_config: Optional[Dict[str, Any]] = None
    ):
        self.seed = seed
        self.num_generations = num_generations
        self.rule_eval_budget = rule_eval_budget
        self.data_dir = Path(data_dir)
        self.results_dir = Path(results_dir)
        
        self.logic_config = logic_config or {}
        self.grid_config = grid_config or {}
        self.agent_config = agent_config or {}
        
        # Validate constraints
        if self.rule_eval_budget <= 0:
            raise ConfigError("rule_eval_budget must be positive")
        if self.num_generations <= 0:
            raise ConfigError("num_generations must be positive")

    def get_seed(self) -> int:
        """Return the global seed."""
        return self.seed

    def set_seed(self) -> None:
        """Apply the seed to random, numpy, and torch (if available)."""
        random.seed(self.seed)
        try:
            import numpy as np
            np.random.seed(self.seed)
        except ImportError:
            pass
        try:
            import torch
            torch.manual_seed(self.seed)
        except ImportError:
            pass

    def to_dict(self) -> Dict[str, Any]:
        """Serialize config to a dictionary."""
        return {
            "seed": self.seed,
            "num_generations": self.num_generations,
            "rule_eval_budget": self.rule_eval_budget,
            "data_dir": str(self.data_dir),
            "results_dir": str(self.results_dir),
            "logic_config": self.logic_config,
            "grid_config": self.grid_config,
            "agent_config": self.agent_config
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Deserialize config from a dictionary."""
        return cls(
            seed=data["seed"],
            num_generations=data["num_generations"],
            rule_eval_budget=data["rule_eval_budget"],
            data_dir=data.get("data_dir", "data"),
            results_dir=data.get("results_dir", "data/results"),
            logic_config=data.get("logic_config"),
            grid_config=data.get("grid_config"),
            agent_config=data.get("agent_config")
        )


def get_default_config() -> Config:
    """
    Returns a default configuration with sensible research defaults.
    
    Returns:
        Config: A valid Config instance.
    """
    return Config(
        seed=42,
        num_generations=50,
        rule_eval_budget=10000,
        data_dir="data",
        results_dir="data/results",
        logic_config={
            "num_proofs": 1000,
            "max_depth": 5,
            "num_vars": 8
        },
        grid_config={
            "grid_size": 10,
            "num_obstacles": 5,
            "num_goals": 1
        },
        agent_config={
            "population_size": 50,
            "mutation_rate": 0.1,
            "crossover_rate": 0.7
        }
    )


def load_config_from_env() -> Config:
    """
    Loads configuration from environment variables.
    
    Environment Variables:
        COEV_SEED: Integer seed.
        COEV_GENERATIONS: Number of generations.
        COEV_BUDGET: Rule evaluation budget.
        COEV_DATA_DIR: Path to data directory.
        
    Returns:
        Config: A Config instance populated from env vars.
        
    Raises:
        ConfigError: If required env vars are missing or invalid.
    """
    try:
        seed = int(os.getenv("COEV_SEED", 42))
        generations = int(os.getenv("COEV_GENERATIONS", 50))
        budget = int(os.getenv("COEV_BUDGET", 10000))
        data_dir = os.getenv("COEV_DATA_DIR", "data")
        results_dir = os.getenv("COEV_RESULTS_DIR", "data/results")
        
        return Config(
            seed=seed,
            num_generations=generations,
            rule_eval_budget=budget,
            data_dir=data_dir,
            results_dir=results_dir
        )
    except ValueError as e:
        raise ConfigError(f"Invalid environment variable value: {e}")


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Loads configuration from a JSON file or environment variables.
    
    Priority:
        1. JSON file if `config_path` is provided.
        2. Environment variables if `config_path` is None.
        3. Defaults if neither exists.
        
    Args:
        config_path: Optional path to a JSON config file.
        
    Returns:
        Config: A valid Config instance.
    """
    if config_path:
        path = Path(config_path)
        if not path.exists():
            raise ConfigError(f"Config file not found: {config_path}")
        
        with open(path, "r") as f:
            data = json.load(f)
        
        return Config.from_dict(data)
    
    # Try environment variables
    if os.getenv("COEV_SEED"):
        return load_config_from_env()
    
    # Fallback to defaults
    return get_default_config()


def save_config(config: Config, config_path: str) -> None:
    """
    Saves the configuration to a JSON file.
    
    Args:
        config: The Config instance to save.
        config_path: Path to the output JSON file.
    """
    path = Path(config_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w") as f:
        json.dump(config.to_dict(), f, indent=2)