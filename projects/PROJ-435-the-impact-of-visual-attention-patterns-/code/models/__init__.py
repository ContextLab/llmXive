"""
Data models for the visual attention study.
Exports Participant, Stimulus, and GazeEvent classes.
"""
from .participant import Participant
from .stimulus import Stimulus
from .gaze_event import GazeEvent

__all__ = ["Participant", "Stimulus", "GazeEvent"]
