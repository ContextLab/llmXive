"""
Utilities for reproducibility: seed management, run ID generation, and data directory handling.
"""
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

def generate_run_id() -> str:
    """
    Generate a unique run ID based on timestamp and a UUID.
    Format: YYYYMMDD_HHMMSS_uuid4
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"{timestamp}_{unique_id}"

def ensure_data_directory(file_path: Path) -> None:
    """
    Ensure the directory for the given file path exists.
    """
    directory = file_path.parent
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)

def set_global_seed(seed: int) -> None:
    """
    Set global random seeds for reproducibility.
    This function should be called at the start of any script.
    """
    import random
    import numpy as np
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass # PyTorch not installed

    random.seed(seed)
    np.random.seed(seed)

def inject_seed_to_log(log_path: Path, seed_info: dict) -> None:
    """
    Inject seed information into an existing run log.
    
    Args:
        log_path: Path to the run log JSON file.
        seed_info: Dictionary containing seed information to inject.
    """
    import json
    
    ensure_data_directory(log_path)
    
    if log_path.exists():
        with open(log_path, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []
    
    if not isinstance(data, list):
        data = []
        
    data.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "seeds": seed_info
    })
    
    with open(log_path, 'w') as f:
        json.dump(data, f, indent=2)
