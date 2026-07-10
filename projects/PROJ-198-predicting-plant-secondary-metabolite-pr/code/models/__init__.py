"""
Pydantic models for the plant secondary metabolite prediction pipeline.

This module defines the core data structures for Species, BGCFeature,
Metabolite, and ModelOutput.
"""
from .species import Species
from .bgc import BGCFeature
from .metabolite import Metabolite
from .output import ModelOutput

__all__ = ["Species", "BGCFeature", "Metabolite", "ModelOutput"]
