"""
Glass Forming Region Prediction Module.

This package contains the core logic for ingesting alloy data,
engineering thermodynamic features, training models, and analyzing results.
"""

from .utils import get_logger, ensure_dir
from .ingestion import run_ingestion
from .features import run_features
from .train import run_training
from .analyze import run_analysis

__all__ = [
    'get_logger', 'ensure_dir',
    'run_ingestion', 'run_features', 'run_training', 'run_analysis'
]
