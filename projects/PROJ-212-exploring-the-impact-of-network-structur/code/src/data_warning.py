import os
import logging
from pathlib import Path
from typing import Dict, Any
import yaml

def check_and_log_warning(raw_dir: Path, threshold: int = 10, log_path: Path = None) -> bool:
    """
    Checks the number of files in the raw data directory.
    If count < threshold, logs a specific warning to logs/warning.log and returns True.
    Otherwise, returns False.
    """
    if log_path is None:
        log_path = raw_dir.parent / "logs" / "warning.log"
    
    # Ensure log directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Count files in raw_dir
    if not raw_dir.exists():
        count = 0
    else:
        # Count only files, not directories
        count = sum(1 for item in raw_dir.iterdir() if item.is_file())

    if count < threshold:
        warning_msg = f"Insufficient data (N<{threshold}). Regression blocked."
        
        # Configure logger specifically for this warning file to avoid duplicating to console if not desired
        # or append to existing root logger. We will use a file handler specifically for this task.
        logger = logging.getLogger("data_warning")
        logger.setLevel(logging.WARNING)
        
        # Remove existing handlers to prevent duplicates if called multiple times in same process
        if not logger.handlers:
            fh = logging.FileHandler(log_path, mode='a')
            formatter = logging.Formatter('%(message)s')
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        
        logger.warning(warning_msg)
        return True
    
    return False

def main():
    """
    Entry point for script execution.
    Reads config to determine paths, checks data availability, and logs warning if needed.
    """
    # Import config to get paths (assuming config.yaml is in root or code/)
    # Based on API surface, we use config.py
    try:
        from config import load_config, get_paths
    except ImportError:
        # Fallback for direct script execution if config is not importable
        # but usually we rely on the project structure
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from config import load_config, get_paths

    config = load_config()
    paths = get_paths(config)
    raw_dir = paths.get('raw_data', paths.get('data_raw'))
    
    if raw_dir is None:
        # Default fallback if config doesn't specify
        raw_dir = Path("data/raw")
    
    # Default threshold from task description
    threshold = config.get('thresholds', {}).get('min_data_count', 10)
    
    check_and_log_warning(raw_dir, threshold)
    print(f"Warning check completed. Raw dir: {raw_dir}, Count: {sum(1 for item in raw_dir.iterdir() if item.is_file()) if raw_dir.exists() else 0}")

if __name__ == "__main__":
    main()