import os
from pathlib import Path
from typing import Final, Dict, Any
from datetime import datetime

# Project root relative to this file
_ROOT = Path(__file__).resolve().parent.parent

def get_config() -> Dict[str, Any]:
    """Return project configuration including paths and seeds."""
    return {
        "root": _ROOT,
        "data_raw": _ROOT / "data" / "raw",
        "data_processed": _ROOT / "data" / "processed",
        "data_artifacts": _ROOT / "data" / "artifacts",
        "code_root": _ROOT / "code",
        "random_seed": 42,
        "start_date": datetime(2010, 1, 1),
        "end_date": datetime(2020, 12, 31),
    }
