import os
from pathlib import Path
from typing import Dict, Any

def load_paths() -> Dict[str, Path]:
    """Loads project paths."""
    project_root = Path(__file__).parent.parent.parent
    return {
        "data_raw": project_root / "data/raw",
        "data_processed": project_root / "data/processed",
        "data_evaluation": project_root / "data/evaluation",
        "code_src": project_root / "code",
        "tests_unit": project_root / "tests/unit",
        "logs": project_root / "data/logs",
    }

def load_env() -> Dict[str, Any]:
    """Loads environment variables."""
    return os.environ

ROW_THRESHOLD = 100000
MIN_ROWS = 1000
RANDOM_SEED = 42
CAP_OUTLIERS = True