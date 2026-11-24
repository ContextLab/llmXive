"""
Data package initialisation.

Exposes the public fetch functions used by the rest of the pipeline.
"""
from .fetch_ace import fetch_ace
from .fetch_noaa import fetch_noaa

__all__ = ["fetch_ace", "fetch_noaa"]