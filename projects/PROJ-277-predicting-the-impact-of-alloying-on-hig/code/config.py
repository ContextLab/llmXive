"""
Configuration management for the alloy oxidation resistance prediction pipeline.

Handles mode-specific constants (ci vs local) and CLI argument parsing.
"""
import argparse
import os
from typing import Dict, Any, Optional

# Default paths relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
FIGURES_DIR = os.path.join(PROJECT_ROOT, "figures")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")

# Mode-specific constants
CONFIG = {
    "ci": {
        "max_rows": 500,
        "random_state": 42,
        "test_size": 0.2,
        "n_jobs": -1,  # Use all available cores in CI
        "downsample_threshold": 500,
        "output_dir": PROCESSED_DATA_DIR,
        "log_level": "INFO",
        "strict_validation": True,
    },
    "local": {
        "max_rows": 1000,
        "random_state": 42,
        "test_size": 0.2,
        "n_jobs": -1,
        "downsample_threshold": 1000,
        "output_dir": PROCESSED_DATA_DIR,
        "log_level": "DEBUG",
        "strict_validation": False,
    },
}

# Default mode
DEFAULT_MODE = "local"


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments for the pipeline.
    
    Returns:
        argparse.Namespace: Parsed arguments including mode and other flags.
    """
    parser = argparse.ArgumentParser(
        description="Predict the impact of alloying on high-temperature oxidation resistance."
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["ci", "local"],
        default=DEFAULT_MODE,
        help="Execution mode: 'ci' for continuous integration (smaller datasets), 'local' for local development.",
    )
    parser.add_argument(
        "--input-file",
        type=str,
        default=None,
        help="Path to input data file. If not provided, defaults to standard raw data location.",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default=None,
        help="Path for output predictions. If not provided, uses default processed data location.",
    )
    parser.add_argument(
        "--skip-fetch",
        action="store_true",
        help="Skip data fetching step if data already exists.",
    )
    parser.add_argument(
        "--skip-train",
        action="store_true",
        help="Skip model training step if model already exists.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output.",
    )
    
    return parser.parse_args()


def get_config(mode: Optional[str] = None) -> Dict[str, Any]:
    """
    Get configuration dictionary for the specified mode.
    
    Args:
        mode: Execution mode ('ci' or 'local'). Defaults to DEFAULT_MODE if None.
        
    Returns:
        Dict[str, Any]: Configuration dictionary for the specified mode.
        
    Raises:
        ValueError: If an invalid mode is provided.
    """
    if mode is None:
        mode = DEFAULT_MODE
        
    if mode not in CONFIG:
        raise ValueError(f"Invalid mode '{mode}'. Must be one of: {list(CONFIG.keys())}")
        
    return CONFIG[mode].copy()


def ensure_directories() -> None:
    """
    Ensure all required directories exist.
    
    Creates directories for raw data, processed data, logs, figures, and models
    if they do not already exist.
    """
    dirs = [
        DATA_DIR,
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        LOGS_DIR,
        FIGURES_DIR,
        MODELS_DIR,
    ]
    
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)


# Convenience function to get config from CLI args
def get_config_from_args(args: Optional[argparse.Namespace] = None) -> Dict[str, Any]:
    """
    Get configuration based on parsed CLI arguments.
    
    Args:
        args: Parsed CLI arguments. If None, parses arguments automatically.
        
    Returns:
        Dict[str, Any]: Configuration dictionary for the specified mode.
    """
    if args is None:
        args = parse_args()
        
    config = get_config(args.mode)
    
    # Override output paths if provided via CLI
    if args.output_file:
        config["output_file"] = args.output_file
        
    if args.input_file:
        config["input_file"] = args.input_file
        
    # Set log level based on verbose flag
    if args.verbose:
        config["log_level"] = "DEBUG"
        
    return config