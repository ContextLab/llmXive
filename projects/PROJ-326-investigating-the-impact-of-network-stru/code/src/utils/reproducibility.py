import json
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .logging import log_run, get_run_log, clear_run_log
from .config import load_config

def ensure_data_directory(data_dir: Optional[Union[str, Path]] = None) -> Path:
    """Ensure the data directory exists."""
    if data_dir is None:
        # Default to project root data/
        project_root = Path(__file__).resolve().parents[2]
        data_dir = project_root / "data"
    else:
        data_dir = Path(data_dir)
    
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def generate_run_id() -> str:
    """Generate a unique run ID based on timestamp and random component."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_component = random.randint(1000, 9999)
    return f"{timestamp}_{random_component}"

def inject_seed_to_log(
    seed: int,
    data_dir: Optional[Union[str, Path]] = None,
    run_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Inject specific random seeds used during a run into data/run_log.json.
    
    This function ensures reproducibility by recording the seed used for a specific run
    directly into the run log, rather than updating the global config.yaml.
    
    Args:
        seed: The random seed value to inject.
        data_dir: Optional path to the data directory. Defaults to project/data.
        run_id: Optional specific run ID. If None, a new one is generated.
        metadata: Optional additional metadata to include with the seed entry.
        
    Returns:
        The updated run log entry for this seed injection.
    """
    # Ensure data directory exists
    data_path = ensure_data_directory(data_dir)
    log_file = data_path / "run_log.json"
    
    # Generate or use provided run ID
    if run_id is None:
        run_id = generate_run_id()
    
    # Prepare the seed entry
    entry = {
        "run_id": run_id,
        "seed": seed,
        "timestamp": datetime.now().isoformat(),
        "source": "seed_injection",
        "metadata": metadata or {}
    }
    
    # Initialize random generators with the seed
    random.seed(seed)
    
    # Log the entry using the logging infrastructure
    # This will append to the run_log.json file
    log_run(entry)
    
    return entry

def get_latest_run_seed(data_dir: Optional[Union[str, Path]] = None) -> Optional[int]:
    """
    Retrieve the seed from the most recent run in the log.
    
    Args:
        data_dir: Optional path to the data directory.
        
    Returns:
        The seed integer if found, None otherwise.
    """
    data_path = ensure_data_directory(data_dir)
    log_file = data_path / "run_log.json"
    
    if not log_file.exists():
        return None
    
    try:
        log_data = get_run_log(data_path)
        if not log_data:
            return None
        
        # Find the most recent entry that contains a seed
        for entry in reversed(log_data):
            if "seed" in entry:
                return entry["seed"]
                
        return None
    except (json.JSONDecodeError, KeyError):
        return None

def verify_reproducibility(
    expected_seed: int,
    data_dir: Optional[Union[str, Path]] = None,
    run_id: Optional[str] = None
) -> bool:
    """
    Verify that a specific seed was recorded in the run log.
    
    Args:
        expected_seed: The seed value to verify.
        data_dir: Optional path to the data directory.
        run_id: Optional specific run ID to check.
        
    Returns:
        True if the seed was found in the log, False otherwise.
    """
    data_path = ensure_data_directory(data_dir)
    log_file = data_path / "run_log.json"
    
    if not log_file.exists():
        return False
    
    try:
        log_data = get_run_log(data_path)
        
        for entry in log_data:
            if entry.get("seed") == expected_seed:
                if run_id is None or entry.get("run_id") == run_id:
                    return True
                    
        return False
    except (json.JSONDecodeError, KeyError):
        return False
