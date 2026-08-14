import os
from pathlib import Path
from typing import Dict, Any


def load_paths() -> Dict[str, Path]:
    """Load and return all project paths as a dictionary."""
    base = Path(__file__).parent.parent
    return {
        "base": base,
        "data": base / "data",
        "code": base / "code",
        "tests": base / "tests",
        "data_raw": base / "data" / "raw",
        "data_processed": base / "data" / "processed",
        "data_evaluation": base / "data" / "evaluation",
        "data_logs": base / "data" / "logs",
        "data_elemental": base / "data" / "elemental_properties",
    }


def load_env() -> Dict[str, str]:
    """Load environment variables into a dictionary."""
    return {
        "MPDS_API_KEY": os.getenv("MPDS_API_KEY", ""),
        "RANDOM_SEED": os.getenv("RANDOM_SEED", "42"),
        "ROW_THRESHOLD": os.getenv("ROW_THRESHOLD", "100000"),
        "CAP_OUTLIERS": os.getenv("CAP_OUTLIERS", "True"),
    }


ROW_THRESHOLD = int(load_env().get("ROW_THRESHOLD", "100000"))
RANDOM_SEED = int(load_env().get("RANDOM_SEED", "42"))
CAP_OUTLIERS = load_env().get("CAP_OUTLIERS", "True").lower() == "true"
