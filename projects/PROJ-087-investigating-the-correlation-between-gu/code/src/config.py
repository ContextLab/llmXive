import os
from typing import Optional, Dict, Any

def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables with defaults."""
    return {
        "DATA_URL": os.getenv("DATA_URL", "https://example.com/data"),
        "RANDOM_SEED": int(os.getenv("RANDOM_SEED", "42")),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        "DATA_PROCESSED_DIR": os.getenv("DATA_PROCESSED_DIR", "data/processed"),
        "DATA_RAW_DIR": os.getenv("DATA_RAW_DIR", "data/raw"),
    }
