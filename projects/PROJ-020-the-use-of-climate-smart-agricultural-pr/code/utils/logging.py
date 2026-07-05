import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

def initialize_logging(log_file: Optional[Path] = None, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("llmXive")
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    return logger

_provenance_cache: List[Dict[str, Any]] = []

def log_provenance_mapping(source: str, target: str, method: str, params: Optional[Dict[str, Any]] = None, timestamp: Optional[str] = None) -> None:
    """
    Log a mapping from a source variable to a target variable with a method and parameters.
    Specifically designed to map component variables (e.g., conservation_tillage_score)
    to their source LSMS question ID and response ID.
    """
    entry = {
        "source": source,
        "target": target,
        "method": method,
        "params": params or {},
        "timestamp": timestamp or datetime.now().isoformat()
    }
    _provenance_cache.append(entry)
    logging.getLogger("llmXive").info(f"Provenance: {source} -> {target} ({method})")

def flush_provenance_cache(output_path: Optional[Path] = None) -> Path:
    """
    Flush the provenance cache to a JSON file.
    Creates a JSON mapping of every component variable to its source LSMS question ID and response ID.
    """
    if output_path is None:
        output_path = Path("state/provenance_log.json")
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(_provenance_cache, f, indent=2)
    
    return output_path

def get_provenance_summary() -> List[Dict[str, Any]]:
    return _provenance_cache

def load_provenance_map(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, 'r') as f:
        return json.load(f)
