import logging
import os
import sys
from pathlib import Path
from typing import Optional
import json

class ProjectConfig:
    """Central configuration class for the project."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.project_id = "PROJ-191-investigating-the-validity-of-the-invers"
        self.code_dir = self.project_root / "code"
        self.data_dir = self.project_root / "data"
        self.results_dir = self.data_dir / "results"
        self.processed_dir = self.data_dir / "processed"
        self.raw_dir = self.data_dir / "raw"
        self.state_dir = self.project_root / "state" / "projects"
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create required directories if they don't exist."""
        directories = [
            self.code_dir,
            self.data_dir,
            self.raw_dir,
            self.processed_dir,
            self.results_dir,
            self.state_dir
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @property
    def arxiv_ids(self) -> list:
        """List of arXiv IDs to process."""
        return ["2106.08611", "2305.06325"]

def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """Configure logging for the project."""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('pipeline.log')
        ]
    )
    return logging.getLogger("project")

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)
