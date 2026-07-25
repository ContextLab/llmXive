"""
Data models for the visual attention and misinformation study.

This module provides dataclasses for Participant, Stimulus, and GazeEvent
to represent the core entities in the eye-tracking experiment.
"""
from .participant import Participant
from .stimulus import Stimulus
from .gaze_event import GazeEvent

__all__ = [
    "Participant",
    "Stimulus",
    "GazeEvent"
]
