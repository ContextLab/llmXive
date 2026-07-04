"""
Data models and entities for the Gut Microbiome-Cognitive Correlation Study.

This module defines the core data structures used throughout the pipeline:
- Participant: Represents a study subject with demographic and clinical data.
- MicrobiomeProfile: Represents microbiome composition data for a participant.
- CognitiveScore: Represents cognitive assessment results for a participant.
"""

from .participant import Participant
from .microbiome import MicrobiomeProfile
from .cognitive import CognitiveScore

__all__ = [
    "Participant",
    "MicrobiomeProfile",
    "CognitiveScore"
]
