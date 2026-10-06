import logging
import os
import sys
from pathlib import Path
from typing import Optional
import json

class ProjectConfig:
    def __init__(self):
        self.project_root = Path(os.getcwd())
        self.data_dir = self.project_root / "data"
        self.code_dir = self.project_root / "code"
        self.state_dir = self.project_root / "state"
        self.inflation_factor = 1.5 # Default, will be overwritten if config exists

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def get_logger(name: str):
    return logging.getLogger(name)
