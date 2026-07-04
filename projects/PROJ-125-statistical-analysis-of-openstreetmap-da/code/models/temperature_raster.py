"""
TemperatureRaster model for storing thermal satellite imagery metadata.
"""
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
import json
from pathlib import Path
from .base import BaseModel
import logging

logger = logging.getLogger(__name__)


@dataclass
class TemperatureRaster(BaseModel):
    """
    Represents a temperature raster derived from satellite thermal imagery.
    
    Attributes:
        name: Unique identifier (e.g., 'LST_MODIS_2023_summer')
        source: Satellite source (e.g., 'MODIS', 'Landsat8', 'Landsat9')
        file_path: Path to the raster file
        acquisition_date: Date of acquisition (ISO format)
        crs: Coordinate Reference System
        resolution: Pixel resolution in meters
        nodata_value: Value representing no-data
        min_temperature: Minimum temperature (Kelvin)
        max_temperature: Maximum temperature (Kelvin)
        mean_temperature: Mean temperature (Kelvin)
        cloud_cover: Percentage of cloud cover (0-100)
        processing_level: Processing level (e.g., 'L2', 'L3')
        units: Temperature units ('K' or 'C')
        metadata: Additional arbitrary metadata
    """
    name: str
    source: str
    file_path: str
    acquisition_date: str
    crs: str
    resolution: float
    nodata_value: float = -9999.0
    min_temperature: Optional[float] = None
    max_temperature: Optional[float] = None
    mean_temperature: Optional[float] = None
    cloud_cover: float = 0.0
    processing_level: str = "L2"
    units: str = "K"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> bool:
        """Validate TemperatureRaster schema."""
        if not self.name or not isinstance(self.name, str):
            logger.error("Temperature raster name must be a non-empty string")
            return False
        
        if not self.source:
            logger.error("Source is required")
            return False
        
        if not self.file_path:
            logger.error("File path is required")
            return False
        
        if not self.acquisition_date:
            logger.error("Acquisition date is required")
            return False
        
        if not self.crs:
            logger.error("CRS is required")
            return False
        
        if self.resolution <= 0:
            logger.error("Resolution must be positive")
            return False
        
        if self.cloud_cover < 0 or self.cloud_cover > 100:
            logger.error("Cloud cover must be between 0 and 100")
            return False
        
        if self.units not in ["K", "C"]:
            logger.warning(f"Unusual temperature unit: {self.units}. Expected 'K' or 'C'.")
        
        # Validate temperature range if provided
        if self.min_temperature is not None and self.max_temperature is not None:
            if self.units == "K":
                if self.min_temperature < 150 or self.max_temperature > 400:
                    logger.warning("Temperature values seem outside typical Earth range for Kelvin")
            elif self.units == "C":
                if self.min_temperature < -50 or self.max_temperature > 70:
                    logger.warning("Temperature values seem outside typical Earth range for Celsius")
        
        return True

    def to_celsius(self) -> "TemperatureRaster":
        """Convert temperature units from Kelvin to Celsius if necessary."""
        if self.units == "K":
            new_min = self.min_temperature - 273.15 if self.min_temperature else None
            new_max = self.max_temperature - 273.15 if self.max_temperature else None
            new_mean = self.mean_temperature - 273.15 if self.mean_temperature else None
            
            return TemperatureRaster(
                name=self.name,
                source=self.source,
                file_path=self.file_path,
                acquisition_date=self.acquisition_date,
                crs=self.crs,
                resolution=self.resolution,
                nodata_value=self.nodata_value,
                min_temperature=new_min,
                max_temperature=new_max,
                mean_temperature=new_mean,
                cloud_cover=self.cloud_cover,
                processing_level=self.processing_level,
                units="C",
                metadata=self.metadata
            )
        return self

    def update_temperatures(self, min_t: float, max_t: float, mean_t: float) -> None:
        """Update temperature statistics."""
        self.min_temperature = min_t
        self.max_temperature = max_t
        self.mean_temperature = mean_t
        logger.info(f"Updated temperatures for {self.name}: min={min_t}, max={max_t}, mean={mean_t}")