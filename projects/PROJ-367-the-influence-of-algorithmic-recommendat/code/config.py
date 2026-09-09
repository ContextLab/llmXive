import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import logging

@dataclass
class ProjectConfig:
    """Central configuration for the project."""
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    seed: int = 42
    synthetic_n_users: int = 5000
    synthetic_n_sessions: int = 10
    semantic_similarity_threshold: float = 0.7
    data_raw_dir: Path = field(init=False)
    data_processed_dir: Path = field(init=False)
    code_dir: Path = field(init=False)

    def __post_init__(self):
        self.data_raw_dir = self.project_root / "data" / "raw"
        self.data_processed_dir = self.project_root / "data" / "processed"
        self.code_dir = self.project_root / "code"

        # Ensure directories exist
        self.data_raw_dir.mkdir(parents=True, exist_ok=True)
        self.data_processed_dir.mkdir(parents=True, exist_ok=True)

def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure project logging."""
    logger = logging.getLogger("llmXive")
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

# Global instance
project_config = ProjectConfig()
