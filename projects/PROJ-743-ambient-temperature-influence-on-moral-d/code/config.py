import os
from pathlib import Path

def get_path_env_override(key: str, default: Path) -> Path:
    """
    Get a path from environment variable or return default.
    """
    val = os.getenv(key)
    if val:
        return Path(val)
    return default

# Configuration for T028a
# If these are not set in env, they default to project root relative paths
PROJECT_ROOT = get_path_env_override("PROJECT_ROOT", Path(__file__).resolve().parent.parent)
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
LOG_DIR = PROJECT_ROOT / "results" / "logs"

# Covariate fetch configuration
COVARIATE_INDICATORS = [
    ("SP.DYN.LE00.IN", "Life Expectancy"),
    ("SP.POP.TOTL", "Total Population")
]

# Geocoding timeout
GEOCODING_TIMEOUT = 10
GEOCODING_USER_AGENT = "llmXive_moral_temp_study"
