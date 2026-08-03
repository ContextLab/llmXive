"""
Raster data models for covariates and temperature targets.
"""
from typing import Optional, Dict, Any, List
import json
from pathlib import Path
import numpy as np
from .base import BaseModel
from config import get_path


class RasterCovariate(BaseModel):
    """
    Model for a raster covariate (e.g., building density, NDVI).
    
    Attributes:
        name: Unique identifier for the covariate
        description: Human-readable description
        source: Data source (e.g., 'OSM', 'Sentinel-2')
        path: Path to the GeoTIFF file
        crs: EPSG code of the CRS
        resolution: Pixel resolution in meters
        nodata_value: Value representing no-data
        min_val: Minimum valid value
        max_val: Maximum valid value
        units: Measurement units (e.g., 'm', '%', 'index')
    """
    
    REQUIRED_FIELDS = ["name", "path", "crs", "resolution"]

    def __init__(
        self,
        name: str,
        description: str,
        source: str,
        path: str,
        crs: int,
        resolution: float,
        nodata_value: float = -9999.0,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        units: str = "unknown",
    ):
        self.name = name
        self.description = description
        self.source = source
        self.path = path
        self.crs = crs
        self.resolution = resolution
        self.nodata_value = nodata_value
        self.min_val = min_val
        self.max_val = max_val
        self.units = units

        self.validate_schema(self.to_dict(), self.REQUIRED_FIELDS)

    def validate_file_exists(self) -> bool:
        """Check if the raster file exists on disk."""
        return Path(self.path).exists()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics for the raster.
        
        Returns:
            Dictionary with min, max, mean, std, count
        """
        if not self.validate_file_exists():
            raise FileNotFoundError(f"Raster file not found: {self.path}")
        
        # Placeholder for actual rasterio logic
        # In a real implementation, this would read the file
        return {
            "min": self.min_val,
            "max": self.max_val,
            "mean": None,
            "std": None,
            "count": None,
            "nodata_count": None,
        }


class TemperatureRaster(BaseModel):
    """
    Model for a temperature raster (LST).
    
    Attributes:
        name: Unique identifier (e.g., 'LST_NYC_2023')
        description: Description of the temperature composite
        source: Satellite source (e.g., 'MODIS', 'Landsat-8')
        path: Path to the GeoTIFF file
        crs: EPSG code
        resolution: Pixel resolution in meters
        nodata_value: No-data value
        min_val: Minimum temperature (K or C)
        max_val: Maximum temperature
        units: Temperature units ('K' or 'C')
        acquisition_date: Date of acquisition (ISO 8601)
        cloud_cover: Average cloud cover percentage
    """
    
    REQUIRED_FIELDS = ["name", "path", "crs", "resolution", "units"]

    def __init__(
        self,
        name: str,
        description: str,
        source: str,
        path: str,
        crs: int,
        resolution: float,
        units: str,
        nodata_value: float = -9999.0,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        acquisition_date: Optional[str] = None,
        cloud_cover: Optional[float] = None,
    ):
        self.name = name
        self.description = description
        self.source = source
        self.path = path
        self.crs = crs
        self.resolution = resolution
        self.units = units
        self.nodata_value = nodata_value
        self.min_val = min_val
        self.max_val = max_val
        self.acquisition_date = acquisition_date
        self.cloud_cover = cloud_cover

        self.validate_schema(self.to_dict(), self.REQUIRED_FIELDS)

        # Validate units
        if self.units not in ["K", "C", "KELVIN", "CELSIUS"]:
            raise ValueError(f"Invalid temperature units: {self.units}. Must be 'K' or 'C'.")

    def validate_file_exists(self) -> bool:
        """Check if the temperature raster file exists on disk."""
        return Path(self.path).exists()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics for the temperature raster.
        
        Returns:
            Dictionary with min, max, mean, std, count
        """
        if not self.validate_file_exists():
            raise FileNotFoundError(f"Temperature file not found: {self.path}")
        
        # Placeholder for actual rasterio logic
        return {
            "min": self.min_val,
            "max": self.max_val,
            "mean": None,
            "std": None,
            "count": None,
            "nodata_count": None,
        }

    def is_valid_temperature(self, value: float) -> bool:
        """
        Check if a value is a valid temperature within physical bounds.
        
        Args:
            value: Temperature value to check
            
        Returns:
            True if valid, False otherwise
        """
        if value == self.nodata_value:
            return False
        
        # Physical bounds (approximate)
        if self.units.upper() in ["K", "KELVIN"]:
            return 180.0 <= value <= 350.0 # ~-93C to 77C
        else:
            return -93.0 <= value <= 77.0
