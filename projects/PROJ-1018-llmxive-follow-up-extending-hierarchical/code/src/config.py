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
    Defines core hyperparameters and paths required for reproducibility and execution.
    """
    seed: int = 42
    chunk_size: int = 2048
    model_path: str = "lmsys/pg-19-test"  # Default to dataset ID or path
    k_clusters: int = 100
    
    # Additional fields for robustness
    max_context_length: int = 32768
    min_document_tokens: int = 32000
    output_dir: str = "data"
    interim_dir: str = "data/interim"
    processed_dir: str = "data/processed"
    figures_dir: str = "figures"
    
    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "json"

    def __post_init__(self):
        """Validate and initialize configuration state."""
        self._set_seed(self.seed)
        self._ensure_directories()

    def _set_seed(self, seed: int) -> None:
        """Set random seeds for reproducibility across libraries."""
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

    def _ensure_directories(self) -> None:
        """Create output directories if they do not exist."""
        for dir_path in [self.output_dir, self.interim_dir, self.processed_dir, self.figures_dir]:
            os.makedirs(dir_path, exist_ok=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary for serialization."""
        return {
            "seed": self.seed,
            "chunk_size": self.chunk_size,
            "model_path": self.model_path,
            "k_clusters": self.k_clusters,
            "max_context_length": self.max_context_length,
            "min_document_tokens": self.min_document_tokens,
            "output_dir": self.output_dir,
            "interim_dir": self.interim_dir,
            "processed_dir": self.processed_dir,
            "figures_dir": self.figures_dir,
            "log_level": self.log_level,
            "log_format": self.log_format,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Load configuration from a dictionary."""
        return cls(
            seed=data.get("seed", 42),
            chunk_size=data.get("chunk_size", 2048),
            model_path=data.get("model_path", "lmsys/pg-19-test"),
            k_clusters=data.get("k_clusters", 100),
            max_context_length=data.get("max_context_length", 32768),
            min_document_tokens=data.get("min_document_tokens", 32000),
            output_dir=data.get("output_dir", "data"),
            interim_dir=data.get("interim_dir", "data/interim"),
            processed_dir=data.get("processed_dir", "data/processed"),
            figures_dir=data.get("figures_dir", "figures"),
            log_level=data.get("log_level", "INFO"),
            log_format=data.get("log_format", "json"),
        )