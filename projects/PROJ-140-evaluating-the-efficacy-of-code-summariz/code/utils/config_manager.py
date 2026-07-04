import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

# Ensure .env is loaded from the project root
# We look for .env in the current working directory or parent directories
def _load_env():
    """Load .env file from project root if it exists."""
    # Try current directory first, then parent directories up to a limit
    current = Path.cwd()
    for _ in range(10):
        env_path = current / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            return
        if current == current.parent:
            break
        current = current.parent

# Load environment variables on module import
_load_env()

class Config:
    """
    Centralized configuration manager for the project.
    Reads values from environment variables with fallback defaults.
    """
    
    # --- Paths ---
    DATA_ROOT: Path = Path(os.getenv("DATA_ROOT", "data"))
    DEFECTS4J_DIR: Path = DATA_ROOT / os.getenv("DEFECTS4J_DIR", "data/defects4j")
    SUMMARIES_DIR: Path = DATA_ROOT / os.getenv("SUMMARIES_DIR", "data/summaries")
    INTERACTION_LOGS_DIR: Path = DATA_ROOT / os.getenv("INTERACTION_LOGS_DIR", "data/interaction_logs")
    ANALYSIS_RESULTS_DIR: Path = DATA_ROOT / os.getenv("ANALYSIS_RESULTS_DIR", "data/analysis_results")
    CONSENT_DIR: Path = DATA_ROOT / os.getenv("CONSENT_DIR", "data/consent")
    STATE_DIR: Path = Path(os.getenv("STATE_DIR", "state/projects/PROJ-140-evaluating-the-efficacy-of-code-summariz"))

    # --- Seeds ---
    RANDOM_SEED: int = int(os.getenv("RANDOM_SEED", "42"))
    LLM_SIM_SEED: int = int(os.getenv("LLM_SIM_SEED", "42"))

    # --- Runtime Flags ---
    ENABLE_RESOURCE_MONITOR: bool = os.getenv("ENABLE_RESOURCE_MONITOR", "true").lower() == "true"
    MAX_RUNTIME_SECONDS: int = int(os.getenv("MAX_RUNTIME_SECONDS", "21600"))
    MAX_RAM_GB: int = int(os.getenv("MAX_RAM_GB", "7"))

    @classmethod
    def ensure_directories(cls) -> None:
        """Ensure all required data directories exist."""
        for dir_path in [
            cls.DATA_ROOT,
            cls.DEFECTS4J_DIR,
            cls.SUMMARIES_DIR,
            cls.INTERACTION_LOGS_DIR,
            cls.ANALYSIS_RESULTS_DIR,
            cls.CONSENT_DIR,
            cls.STATE_DIR
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Return configuration as a dictionary."""
        return {
            "DATA_ROOT": str(cls.DATA_ROOT),
            "DEFECTS4J_DIR": str(cls.DEFECTS4J_DIR),
            "SUMMARIES_DIR": str(cls.SUMMARIES_DIR),
            "INTERACTION_LOGS_DIR": str(cls.INTERACTION_LOGS_DIR),
            "ANALYSIS_RESULTS_DIR": str(cls.ANALYSIS_RESULTS_DIR),
            "CONSENT_DIR": str(cls.CONSENT_DIR),
            "STATE_DIR": str(cls.STATE_DIR),
            "RANDOM_SEED": cls.RANDOM_SEED,
            "LLM_SIM_SEED": cls.LLM_SIM_SEED,
            "ENABLE_RESOURCE_MONITOR": cls.ENABLE_RESOURCE_MONITOR,
            "MAX_RUNTIME_SECONDS": cls.MAX_RUNTIME_SECONDS,
            "MAX_RAM_GB": cls.MAX_RAM_GB,
        }

# Singleton instance for easy access
_config_instance: Optional[Config] = None

def get_config() -> Config:
    """
    Returns the singleton Config instance.
    Ensures directories are created on first access if needed.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
        _config_instance.ensure_directories()
    return _config_instance