from dataclasses import dataclass
from typing import Dict, Any
import os
import random
import numpy as np
import torch

@dataclass
class Config:
    """
    Central configuration for the hierarchical sparse attention pipeline.
    """
    seed: int = 42
    chunk_size: int = 2048
    model_path: str = "lmsys/pg-19-test"
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

    # Fields required by T001
    min_tokens: int = 32000
    skip_short_documents: bool = True
    PAD_SHORT_DOCS: bool = False

    def __post_init__(self):
        """Validate configuration and set deterministic seeds."""
        assert self.skip_short_documents, (
            "skip_short_documents must be True according to the task specification."
        )
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
        for dir_path in [
            self.output_dir,
            self.interim_dir,
            self.processed_dir,
            self.figures_dir,
        ]:
            os.makedirs(dir_path, exist_ok=True)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize configuration to a plain dictionary."""
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
            "min_tokens": self.min_tokens,
            "skip_short_documents": self.skip_short_documents,
            "PAD_SHORT_DOCS": self.PAD_SHORT_DOCS,
        }
