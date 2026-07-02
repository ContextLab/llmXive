"""
Utility functions for the avian song variation project.
Includes logging setup, random state pinning, memory monitoring, and project structure creation.
"""
import os
import sys
import shutil
import logging
import random
import time
import tracemalloc
from pathlib import Path
from typing import Optional, Dict, Any, List

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Setup basic logging configuration.
    If log_file is provided, logs are written to that file as well.
    """
    logger = logging.getLogger("avian_song_project")
    logger.setLevel(level)
    
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def pin_random_state(seed: int = 42) -> None:
    """
    Pin random seeds for reproducibility across numpy, random, etc.
    Note: numpy is imported dynamically if needed to avoid circular deps in utils.
    """
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    
    # Set environment variable for libraries that respect it
    os.environ["PYTHONHASHSEED"] = str(seed)

def start_memory_monitor() -> None:
    """
    Start memory monitoring using tracemalloc.
    """
    tracemalloc.start()

def record_memory_snapshot() -> Dict[str, Any]:
    """
    Record current memory usage snapshot.
    Returns a dictionary with current and peak memory in MB.
    """
    if not tracemalloc.is_tracing():
        return {"current_mb": 0.0, "peak_mb": 0.0, "status": "not_monitoring"}
    
    current, peak = tracemalloc.get_traced_memory()
    return {
        "current_mb": current / 1024 / 1024,
        "peak_mb": peak / 1024 / 1024,
        "status": "monitoring"
    }

def stop_memory_monitor() -> Dict[str, Any]:
    """
    Stop memory monitoring and return final stats.
    """
    if not tracemalloc.is_tracing():
        return {"status": "not_monitoring"}
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    return {
        "final_current_mb": current / 1024 / 1024,
        "final_peak_mb": peak / 1024 / 1024,
        "status": "stopped"
    }

def get_memory_usage_mb() -> float:
    """
    Get current memory usage in MB without stopping the monitor.
    Returns 0.0 if not monitoring.
    """
    if not tracemalloc.is_tracing():
        return 0.0
    
    current, _ = tracemalloc.get_traced_memory()
    return current / 1024 / 1024

def get_project_paths() -> Dict[str, Path]:
    """
    Return a dictionary of standard project paths.
    """
    base = Path.cwd()
    return {
        "root": base,
        "code": base / "code",
        "data_raw": base / "data" / "raw",
        "data_processed": base / "data" / "processed",
        "output": base / "output",
        "output_logs": base / "output" / "logs",
        "output_models": base / "output" / "models",
        "output_reports": base / "output" / "reports",
        "figures": base / "figures",
        "tests": base / "tests",
        "specs": base / "specs" / "001-predicting-avian-song-variation",
        "contracts": base / "specs" / "001-predicting-avian-song-variation" / "contracts"
    }

def create_project_structure() -> None:
    """
    Create the standard directory structure for the project if it doesn't exist.
    """
    paths = get_project_paths()
    
    directories = [
        paths["code"],
        paths["data_raw"],
        paths["data_processed"],
        paths["output"],
        paths["output_logs"],
        paths["output_models"],
        paths["output_reports"],
        paths["figures"],
        paths["tests"],
        paths["specs"],
        paths["contracts"]
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Create a .gitkeep file in each directory to ensure they are tracked
    for directory in directories:
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

def setup_logging_infrastructure() -> None:
    """
    Ensure log directories exist and setup basic logging.
    """
    paths = get_project_paths()
    paths["output_logs"].mkdir(parents=True, exist_ok=True)
    
    # Setup default loggers
    setup_logging(paths["output_logs"] / "ingestion.log", level=logging.INFO)
    setup_logging(paths["output_logs"] / "modeling.log", level=logging.INFO)

def safe_mkdir(path: Path) -> None:
    """
    Safely create a directory, including parents if needed.
    """
    path.mkdir(parents=True, exist_ok=True)

def file_exists(path: Path) -> bool:
    """
    Check if a file exists.
    """
    return path.exists() and path.is_file()

def directory_exists(path: Path) -> bool:
    """
    Check if a directory exists.
    """
    return path.exists() and path.is_dir()
