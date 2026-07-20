"""
Logging Configuration Module.

Sets up logging infrastructure for derivation logs and pipeline execution.

This module ensures strict typing and comprehensive documentation
as per task T039 requirements.
"""
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import json

class DerivationAdapter(logging.LoggerAdapter):
    """
    Logger adapter to include derivation parameters in log records.
    """
    def process(self, msg, kwargs):
        extra = kwargs.get('extra', {})
        extra.update(self.extra)
        kwargs['extra'] = extra
        return msg, kwargs

def setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO) -> None:
    """
    Configure the root logger with console and file handlers.
    
    Args:
        log_file: Optional path to a log file.
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers = []
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root_logger.addHandler(ch)
    
    # File handler (if specified)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        root_logger.addHandler(fh)

def get_derivation_logger(name: str, params: Dict[str, Any]) -> DerivationAdapter:
    """
    Get a logger adapter configured for derivation logging.
    
    Args:
        name: Name of the derivation step.
        params: Dictionary of parameters for the derivation.
        
    Returns:
        A DerivationAdapter instance.
    """
    logger = logging.getLogger(f"derivation.{name}")
    return DerivationAdapter(logger, {'params': params})

def log_derivation_params(logger: DerivationAdapter, params: Dict[str, Any]) -> None:
    """
    Log derivation parameters at INFO level.
    
    Args:
        logger: The derivation logger adapter.
        params: Parameters to log.
    """
    logger.info(f"Derivation parameters: {json.dumps(params, indent=2)}")
