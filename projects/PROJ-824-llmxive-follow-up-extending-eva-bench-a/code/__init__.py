"""
llmXive EVA-Bench extension package.

This package provides tools for injecting latency and acoustic perturbations
into EVA-Bench audio streams for robustness evaluation.
"""
from code.config import ensure_directories, PROJECT_ROOT
from code.logging_config import setup_logging

__version__ = "0.1.0"
__all__ = ["ensure_directories", "PROJECT_ROOT", "setup_logging"]
