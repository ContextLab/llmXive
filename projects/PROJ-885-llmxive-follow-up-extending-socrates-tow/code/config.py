"""
Configuration module for llmXive Dynamic Socio-Cognitive State Injection pipeline.
Contains pinned random seeds, file paths, and hyperparameters.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging
import logging.handlers

# ============================================================================
# Random Seeds (Reproducibility)
# ============================================================================
# Pinned seed for deterministic behavior across runs
RANDOM_SEED = 42

# Set seeds for standard libraries
def set_all_seeds(seed: int = RANDOM_SEED) -> None:
    """Set random seeds for reproducibility across Python, NumPy (if available), and random."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

# ============================================================================
# File Paths
# ============================================================================
# Project root is assumed to be the parent of 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
SPECS_DIR = PROJECT_ROOT / "specs"

# Ensure directories exist
def ensure_directories() -> None:
    """Create all required data directories if they don't exist."""
    for dir_path in [DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_RESULTS_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Hyperparameters
# ============================================================================
# Data Generation
GENERATION_CONFIG = {
    "num_trajectories": 1000,
    "oversampling_target_high_emotional": 0.40,
    "oversampling_target_diverse_cultural": 0.40,
    "max_turns_per_trajectory": 10,
    "min_turns_per_trajectory": 3,
}

# Classifier Training
CLASSIFIER_CONFIG = {
    "train_test_split": 0.8,
    "random_state": RANDOM_SEED,
    "tfidf_max_features": 5000,
    "tfidf_ngram_range": (1, 2),
}

# Experiment Runner
EXPERIMENT_CONFIG = {
    "turns_between_inference": 2,
    "low_confidence_threshold": 0.65,
    "max_retries": 3,
    "retry_base_delay": 1.0,
    "retry_max_delay": 10.0,
    "memory_limit_gb": 7.0,
}

# Model Configuration
# List of models to attempt loading (filtered by memory in model_loader.py)
AVAILABLE_MODELS = [
    "google-t5/t5-small",       # ~240MB
    "microsoft/phi-1.5",        # ~3GB (might be close to limit)
    "facebook/opt-1.3b",        # ~2.6GB
    "stabilityai/stablelm-3b-4e1t", # ~6GB (might be excluded)
]

# ============================================================================
# Logging Configuration
# ============================================================================
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE_DIR = DATA_RESULTS_DIR / "logs"

# Custom filter to track specific experiment conditions
class ExperimentConditionFilter(logging.Filter):
    """
    A logging filter that allows logging based on experiment condition (Adapter vs. Static).
    Also tracks skipped samples by logging a specific marker.
    """
    def __init__(self, condition: Optional[str] = None, allow_skipped: bool = True):
        super().__init__()
        self.condition = condition
        self.allow_skipped = allow_skipped

    def filter(self, record: logging.LogRecord) -> bool:
        # If tracking a specific condition, check if the log message contains it
        if self.condition:
            if self.condition.lower() not in record.getMessage().lower():
                # If the message doesn't mention the condition, we might still want to log
                # general info, but we can tag it. For now, allow all but tag if needed.
                pass 
        
        # Track skipped samples
        if not self.allow_skipped and "skipped" in record.getMessage().lower():
            return False
        
        return True

def setup_logging(log_level: int = LOG_LEVEL, log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure logging infrastructure.
    
    Sets up:
    1. Console handler with standard format.
    2. Rotating file handler in data/results/logs if a path is provided.
    3. Custom filters to track experiment conditions (Adapter/Static) and skipped samples.
    
    Args:
        log_level: Logging level (e.g., logging.INFO, logging.DEBUG)
        log_file: Optional path to log file. If None, logs to console only.
    
    Returns:
        A configured logger instance.
    """
    # Ensure log directory exists
    LOG_FILE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger("llmXive")
    logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates in interactive environments
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        # Use RotatingFileHandler to prevent log files from growing indefinitely
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(file_handler)
    
    # Add custom filters for experiment tracking
    # Filter for Adapter condition
    adapter_filter = ExperimentConditionFilter(condition="Adapter")
    logger.addFilter(adapter_filter)
    
    # Filter for Static condition
    static_filter = ExperimentConditionFilter(condition="Static")
    logger.addFilter(static_filter)
    
    return logger

# ============================================================================
# Utility Functions
# ============================================================================
def get_config_summary() -> Dict[str, Any]:
    """Return a dictionary summary of current configuration."""
    return {
        "random_seed": RANDOM_SEED,
        "paths": {
            "project_root": str(PROJECT_ROOT),
            "data_raw": str(DATA_RAW_DIR),
            "data_processed": str(DATA_PROCESSED_DIR),
            "data_results": str(DATA_RESULTS_DIR),
        },
        "generation": GENERATION_CONFIG,
        "classifier": CLASSIFIER_CONFIG,
        "experiment": EXPERIMENT_CONFIG,
        "models": AVAILABLE_MODELS,
    }

# Initialize seeds on module import
set_all_seeds()
ensure_directories()

# Default logger instance
logger = setup_logging()