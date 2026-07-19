import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

def initialize_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    # File handler
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_handler = logging.FileHandler(LOG_DIR / f"{name}_{timestamp}.log")
    file_handler.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

_provenance_cache: Dict[str, Dict[str, Any]] = {}

def log_provenance_mapping(derived_var: str, source_id: str, response_id: Optional[str] = None) -> None:
    _provenance_cache[derived_var] = {
        "source_id": source_id,
        "response_id": response_id,
        "timestamp": datetime.now().isoformat()
    }

def flush_provenance_cache(output_path: Optional[Path] = None) -> None:
    if output_path is None:
        output_path = Path("data/state/provenance_map.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(_provenance_cache, f, indent=2)

def get_provenance_summary() -> Dict[str, Any]:
    return _provenance_cache

def load_provenance_map(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return json.load(f)
