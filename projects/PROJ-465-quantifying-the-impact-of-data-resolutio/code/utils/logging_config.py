"""
Logging configuration for the research pipeline.
"""
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

class DerivationAdapter(logging.LoggerAdapter):
    """Logger adapter for derivation-specific metadata."""
    def process(self, msg, kwargs):
        extra = kwargs.get('extra', {})
        extra.update(self.extra)
        kwargs['extra'] = extra
        return msg, kwargs

def setup_logging(log_level: int = logging.INFO, log_dir: Optional[Path] = None):
    """Configure root logger with console and optional file handlers."""
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_dir / 'pipeline.log')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

def get_derivation_logger(name: str, derivation_params: Optional[Dict[str, Any]] = None) -> DerivationAdapter:
    """Get a logger configured for derivation logging."""
    base_logger = logging.getLogger(name)
    extra = derivation_params or {}
    return DerivationAdapter(base_logger, extra)

def log_derivation_params(logger: DerivationAdapter, params: Dict[str, Any]):
    """Log derivation parameters."""
    logger.info(f"Derivation parameters: {params}")
