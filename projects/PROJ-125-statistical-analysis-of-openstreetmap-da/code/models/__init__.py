"""
Data models and schema validation for the Urban Heat Island OSM analysis pipeline.

This module provides Pydantic-based data models for:
- CityBoundary: Geospatial boundaries for study areas
- RasterCovariate: Vector-derived covariates rasterized to grid
- TemperatureRaster: Thermal imagery and land-surface temperature data
"""
from .base import BaseModel
from .city_boundary import CityBoundary
from .raster_covariate import RasterCovariate
from .temperature_raster import TemperatureRaster

__all__ = [
    "BaseModel",
    "CityBoundary",
    "RasterCovariate",
    "TemperatureRaster",
]
