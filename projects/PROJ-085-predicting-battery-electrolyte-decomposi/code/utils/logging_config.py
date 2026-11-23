"""
Minimal logging configuration for the project.

The project already provides a ``llmxive_toolkit.get_logger`` helper that
creates a logger with sensible defaults (file, console, formatting).  This
module wraps that helper and offers a few convenience functions used by
the descriptor and evaluation code.
"""

from llmxive_toolkit import get_logger as _toolkit_get_logger

def get_logger(name: str):
    """
    Return a logger instance for the given ``name``.

    The underlying implementation is delegated to ``llmxive_toolkit``.
    """
    return _toolkit_get_logger(name)


def log_missing_geometric_data(message: str):
    """
    Log a warning when geometric information cannot be extracted.
    """
    logger = get_logger(__name__)
    logger.warning(f"Missing geometric data: {message}")


def log_metallic_outlier(count: int):
    """
    Log a warning about rows flagged as metallic (zero/negative band gap).
    """
    logger = get_logger(__name__)
    logger.warning(f"Metallic outlier detected in {count} rows (band_gap <= 0).")


def log_feature_extraction_error(message: str):
    """
    Log an error that occurred during feature extraction.
    """
    logger = get_logger(__name__)
    logger.error(f"Feature extraction error: {message}")
