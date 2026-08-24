"""
Data models and entities for the Gut Microbiome-Cognitive Correlation Study.

This module defines the core data structures used throughout the pipeline:
- Participant: Demographic and clinical information
- MicrobiomeProfile: Taxonomic abundance data
- CognitiveScore: Cognitive assessment results
"""

from .participant import Participant
from .microbiome import MicrobiomeProfile
from .cognitive import CognitiveScore

__all__ = [
    'Participant',
    'MicrobiomeProfile',
    'CognitiveScore'
]
