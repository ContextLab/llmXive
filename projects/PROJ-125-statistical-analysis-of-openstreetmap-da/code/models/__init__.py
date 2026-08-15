"""
Data models and schema validation for the Urban Heat Island analysis pipeline.
"""
from .base import BaseModel
from .city import CityBoundary
from .raster import RasterCovariate, TemperatureRaster

__all__ = [
    "BaseModel",
    "CityBoundary",
    "RasterCovariate",
    "TemperatureRaster",
]
