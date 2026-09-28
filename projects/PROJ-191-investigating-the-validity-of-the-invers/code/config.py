import logging
import os
import sys
from pathlib import Path
from typing import Optional
import json

class ProjectConfig:
    def __init__(self):
        self.root = Path(__file__).resolve().parent.parent
        self.data_raw = self.root / "data" / "raw"
        self.data_processed = self.root / "data" / "processed"
        self.data_results = self.root / "data" / "results"
        self.code_dir = self.root / "code"
        
        # Ensure directories exist
        for d in [self.data_raw, self.data_processed, self.data_results]:
            d.mkdir(parents=True, exist_ok=True)
        
        # Load configuration from JSON if it exists
        self.config_path = self.root / "config.json"
        self.settings = {}
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.settings = json.load(f)
        else:
            # Default settings
            self.settings = {
                "log_level": "INFO",
                "log_file": None,
                "inference_timeout_hours": 6.0,
                "bootstrap_flag": False,
                "inflation_factor": 1.1
            }
            self.save_config()

    def save_config(self):
        """Save current settings to config.json"""
        with open(self.config_path, 'w') as f:
            json.dump(self.settings, f, indent=2)

    def get_log_level(self) -> int:
        level_str = self.settings.get("log_level", "INFO").upper()
        return getattr(logging, level_str, logging.INFO)

    def get_log_file(self) -> Optional[str]:
        return self.settings.get("log_file")

    def get_inference_timeout(self) -> float:
        return self.settings.get("inference_timeout_hours", 6.0) * 3600

    def is_bootstrap_needed(self) -> bool:
        return self.settings.get("bootstrap_flag", False)

    def set_bootstrap_flag(self, value: bool):
        self.settings["bootstrap_flag"] = value
        self.save_config()

    def get_inflation_factor(self) -> float:
        return self.settings.get("inflation_factor", 1.1)

    def set_inflation_factor(self, value: float):
        self.settings["inflation_factor"] = value
        self.save_config()

# Global logger instance (initialized on first call)
_logger_initialized = False
_logger_level = logging.INFO
_logger_file = None

def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None) -> None:
    """
    Configure logging for the project.
    Sets up handlers for console and optional file output.
    """
    global _logger_initialized, _logger_level, _logger_file
    
    _logger_level = level
    _logger_file = log_file
    
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers,
        force=True
    )
    _logger_initialized = True

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    Initializes logging if not already done, using config defaults if available.
    """
    global _logger_initialized, _logger_level, _logger_file
    
    # Try to initialize if not done yet
    if not _logger_initialized:
        # Check if we have a ProjectConfig available
        try:
            config = ProjectConfig()
            level = config.get_log_level()
            log_file = config.get_log_file()
            setup_logging(level, log_file)
        except Exception:
            # Fallback to default if config not available
            setup_logging(logging.INFO, None)
    
    return logging.getLogger(name)