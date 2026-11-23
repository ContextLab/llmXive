"""
Configuration module for llmXive ProRL pipeline.

Defines default hyperparameters and provides functionality to load
configuration from YAML files.
"""
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import yaml


@dataclass
class ProRLConfig:
    """
    Configuration container for ProRL hyperparameters.
    
    Attributes:
        path_length (int): Maximum length of recommendation paths (L).
        alpha (float): Position-specific advantage scaling factor.
        beam_width (int): Number of candidates to keep during beam search.
        random_seed (int): Seed for reproducibility.
        similarity_threshold (float): Minimum similarity score to consider an edge.
        max_items (int): Maximum number of items to process (for resource enforcement).
    """
    path_length: int = 5
    alpha: float = 0.1
    beam_width: int = 50
    random_seed: int = 42
    similarity_threshold: float = 0.01
    max_items: int = 500000
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "path_length": self.path_length,
            "alpha": self.alpha,
            "beam_width": self.beam_width,
            "random_seed": self.random_seed,
            "similarity_threshold": self.similarity_threshold,
            "max_items": self.max_items,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProRLConfig":
        """Create configuration from dictionary."""
        return cls(
            path_length=data.get("path_length", cls.path_length),
            alpha=data.get("alpha", cls.alpha),
            beam_width=data.get("beam_width", cls.beam_width),
            random_seed=data.get("random_seed", cls.random_seed),
            similarity_threshold=data.get("similarity_threshold", cls.similarity_threshold),
            max_items=data.get("max_items", cls.max_items),
        )


def load_config(config_path: Optional[str] = None) -> ProRLConfig:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the YAML configuration file. If None, returns
                    default configuration.
                    
    Returns:
        ProRLConfig: Configuration object with loaded or default values.
        
    Raises:
        FileNotFoundError: If the specified config file does not exist.
        yaml.YAMLError: If the config file contains invalid YAML.
    """
    if config_path is None:
        return ProRLConfig()
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    if data is None:
        return ProRLConfig()
    
    return ProRLConfig.from_dict(data)


def save_config(config: ProRLConfig, config_path: str) -> None:
    """
    Save configuration to a YAML file.
    
    Args:
        config: Configuration object to save.
        config_path: Path where the YAML file should be written.
    """
    os.makedirs(os.path.dirname(config_path) if os.path.dirname(config_path) else ".", exist_ok=True)
    
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False, sort_keys=False)


# Default configuration instance
DEFAULT_CONFIG = ProRLConfig()
