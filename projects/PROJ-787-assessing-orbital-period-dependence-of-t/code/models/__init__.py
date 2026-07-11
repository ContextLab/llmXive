"""
Models package for exoplanet data structures.

Provides dataclasses for PlanetRecord and GapResult matching
the project's JSON schemas.
"""
from .planet_record import PlanetRecord
from .gap_result import GapResult

__all__ = ["PlanetRecord", "GapResult"]
