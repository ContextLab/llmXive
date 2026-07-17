"""
llmXive - Predicting Molecular Surface Area from Graph Convolutional Networks

This package provides the core infrastructure for ingesting molecular data,
preprocessing graphs, training GCN models, and evaluating performance against
geometry-based baselines.
"""

import os
import sys
from pathlib import Path

# Ensure the code directory is in the path for relative imports if run as script
_code_root = Path(__file__).parent
if str(_code_root) not in sys.path:
    sys.path.insert(0, str(_code_root))

from .utils.config import load_env_config, get_project_root, get_data_dir, get_results_dir

__version__ = "0.1.0"
__author__ = "llmXive Research Team"

__all__ = [
    "load_env_config",
    "get_project_root",
    "get_data_dir",
    "get_results_dir",
    "load_env_config",
]
