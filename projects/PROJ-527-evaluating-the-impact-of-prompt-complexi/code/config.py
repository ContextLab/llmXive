"""
Configuration management for the project.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np

# Fixed random seeds for reproducibility
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

# Project Root
# Assumes the script is run from the project root or the code directory
# We define paths relative to the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# If running from code/, parent is code, parent.parent is root.
# If running from root, parent is root.
if PROJECT_ROOT.name == "code":
    PROJECT_ROOT = PROJECT_ROOT.parent

# Directories
class Paths:
    ROOT = PROJECT_ROOT
    DATA_RAW = ROOT / "data" / "raw"
    DATA_PROCESSED = ROOT / "data" / "processed"
    DATA_RESULTS = ROOT / "data" / "results"
    STATE = ROOT / "state" / "projects"
    CODE = ROOT / "code"
    TESTS = ROOT / "tests"
    FIGURES = ROOT / "figures"
    SPECS = ROOT / "specs"

    @classmethod
    def ensure_dirs(cls):
        cls.DATA_RAW.mkdir(parents=True, exist_ok=True)
        cls.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
        cls.DATA_RESULTS.mkdir(parents=True, exist_ok=True)
        cls.STATE.mkdir(parents=True, exist_ok=True)
        cls.FIGURES.mkdir(parents=True, exist_ok=True)

def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    return os.environ.get(key, default)

class Config:
    @staticmethod
    def get_project_id() -> str:
        # Read from plan.md or default
        # For now, we assume the project ID is derived from the directory name or a constant
        # The task T009a mentions reading from plan.md first line or config constant
        # We'll use a fallback constant if plan.md is not parsed here
        return "PROJ-527-evaluating-the-impact-of-prompt-complexi"

    @staticmethod
    def get_api_keys() -> Dict[str, str]:
        return {
            "HF_TOKEN": get_env_var("HF_TOKEN"),
            "OPENAI_API_KEY": get_env_var("OPENAI_API_KEY")
        }

def get_config_summary() -> Dict[str, Any]:
    return {
        "random_seed": RANDOM_SEED,
        "project_id": Config.get_project_id(),
        "paths": {
            "data_raw": str(Paths.DATA_RAW),
            "data_processed": str(Paths.DATA_PROCESSED),
            "data_results": str(Paths.DATA_RESULTS)
        }
    }