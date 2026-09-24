from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import os
import random
import numpy as np
import torch


@dataclass
class Config:
    """
    Base configuration manager for the llmXive hierarchical sparse attention pipeline.
    
    Attributes:
        seed (int): Random seed for reproducibility across numpy, torch, and python.
        chunk_size (int): Size of text chunks for processing (default 2048).
        model_path (str): Path or identifier for the pre-trained HiLS model.
        k_clusters (int): Number of clusters for K-Means static index construction.
        data_root (str): Root directory for data artifacts (raw, interim, processed).
        output_dir (str): Directory for output artifacts.
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR).
    """
    seed: int = 42
    chunk_size: int = 2048
    model_path: str = "lmsys/pg-19-test"  # Default to dataset identifier, overridden for model
    k_clusters: int = 100
    data_root: str = "data"
    output_dir: str = "data/processed"
    log_level: str = "INFO"
    
    def __post_init__(self):
        """Initialize random states based on the seed."""
        random.seed(self.seed)
        np.random.seed(self.seed)
        torch.manual_seed(self.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.seed)
        
        # Ensure data directories exist if paths are relative
        if not os.path.isabs(self.data_root):
            # Resolve relative to project root or current working directory
            full_data_root = os.path.abspath(self.data_root)
            if not os.path.exists(full_data_root):
                os.makedirs(full_data_root, exist_ok=True)
            
            interim_dir = os.path.join(full_data_root, "interim")
            if not os.path.exists(interim_dir):
                os.makedirs(interim_dir, exist_ok=True)
                
            processed_dir = os.path.join(full_data_root, "processed")
            if not os.path.exists(processed_dir):
                os.makedirs(processed_dir, exist_ok=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary for serialization."""
        return {
            "seed": self.seed,
            "chunk_size": self.chunk_size,
            "model_path": self.model_path,
            "k_clusters": self.k_clusters,
            "data_root": self.data_root,
            "output_dir": self.output_dir,
            "log_level": self.log_level
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create a Config instance from a dictionary."""
        return cls(
            seed=data.get("seed", 42),
            chunk_size=data.get("chunk_size", 2048),
            model_path=data.get("model_path", "lmsys/pg-19-test"),
            k_clusters=data.get("k_clusters", 100),
            data_root=data.get("data_root", "data"),
            output_dir=data.get("output_dir", "data/processed"),
            log_level=data.get("log_level", "INFO")
        )