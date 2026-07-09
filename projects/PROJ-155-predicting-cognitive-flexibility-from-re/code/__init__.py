"""
llmXive Cognitive Flexibility Pipeline
"""

__version__ = "0.1.0"

from code.config import get_config
from code.data import load_nifti, load_behavioral_csv

__all__ = [
    "get_config",
    "load_nifti",
    "load_behavioral_csv",
]