"""
Utils module for the Cross-Modal Comparison of Neural Prediction Error Signals project.

This package provides shared utilities such as logging, configuration loading,
and common helper functions.
"""

# Initialize logging infrastructure if not already done by data module
# This ensures that code.utils.logger can be imported independently if needed.
try:
    from ..data import get_logger, logger
except ImportError:
    # Fallback if data module isn't loaded yet (rare, but safe)
    import logging
    import os
    from pathlib import Path

    _logger = None

    def get_logger(name: str = "llmXive.utils") -> logging.Logger:
        global _logger
        if _logger is None:
            project_root = Path(__file__).resolve().parent.parent
            log_dir = project_root / "data" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "data_pipeline.log"

            _logger = logging.getLogger(name)
            _logger.setLevel(logging.INFO)

            if not _logger.handlers:
                fh = logging.FileHandler(log_file)
                fh.setLevel(logging.INFO)
                ch = logging.StreamHandler()
                ch.setLevel(logging.WARNING)

                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S"
                )
                fh.setFormatter(formatter)
                ch.setFormatter(formatter)

                _logger.addHandler(fh)
                _logger.addHandler(ch)
        return _logger

    logger = get_logger()

__all__ = ["get_logger", "logger"]
