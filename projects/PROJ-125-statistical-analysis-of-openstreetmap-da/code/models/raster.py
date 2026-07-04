"""
Raster data models.
"""
from typing import Optional, Dict, Any, List
import json
from pathlib import Path
import numpy as np
from .base import BaseModel
from config import get_path

class RasterCovariate(BaseModel):
    """
    Represents a raster covariate layer (e.g., building density, NDVI).
    """
    
    def __init__(
        self,
        name: str,
        path: Path,
        band: int = 1,
        crs: Optional[str] = None,
        resolution: Optional[float] = None,
        description: Optional[str] = None
    ):
        """
        Initialize RasterCovariate.
        
        Args:
            name: Unique name for the covariate
            path: Path to the raster file
            band: Band index (1-based)
            crs: Coordinate Reference System
            resolution: Resolution in meters
            description: Human-readable description
        """
        super().__init__()
        self.name = name
        self.path = path
        self.band = band
        self.crs = crs
        self.resolution = resolution
        self.description = description or name
        
        if not self.path.exists():
            raise FileNotFoundError(f"Raster file not found: {self.path}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": str(self.path),
            "band": self.band,
            "crs": self.crs,
            "resolution": self.resolution,
            "description": self.description
        }

class TemperatureRaster(BaseModel):
    """
    Represents the target variable: Land Surface Temperature raster.
    """
    
    def __init__(
        self,
        path: Path,
        crs: Optional[str] = None,
        resolution: Optional[float] = None,
        date_range: Optional[Dict[str, str]] = None,
        unit: str = "Kelvin"
    ):
        """
        Initialize TemperatureRaster.
        
        Args:
            path: Path to the temperature raster file
            crs: Coordinate Reference System
            resolution: Resolution in meters
            date_range: Dict with 'start' and 'end' keys
            unit: Temperature unit (default: Kelvin)
        """
        super().__init__()
        self.path = path
        self.crs = crs
        self.resolution = resolution
        self.date_range = date_range or {}
        self.unit = unit
        
        if not self.path.exists():
            raise FileNotFoundError(f"Temperature raster not found: {self.path}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": str(self.path),
            "crs": self.crs,
            "resolution": self.resolution,
            "date_range": self.date_range,
            "unit": self.unit
        }