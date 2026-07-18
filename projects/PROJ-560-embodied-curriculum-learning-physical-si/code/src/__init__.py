"""
Embodied Curriculum Learning: Physical Simulation for Abstract Concept Teaching
Core source package.
"""

from .logging_config import setup_logging
from .models import DatasetRecord, AnalysisResult, SensitivitySweep
from .utils import set_seed

__all__ = [
    "setup_logging",
    "DatasetRecord",
    "AnalysisResult",
    "SensitivitySweep",
    "set_seed",
]
