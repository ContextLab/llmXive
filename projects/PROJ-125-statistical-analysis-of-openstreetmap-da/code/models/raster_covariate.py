"""
RasterCovariate model for storing OSM-derived covariate raster metadata.
"""
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
import json
from pathlib import Path
from .base import BaseModel
import logging

logger = logging.getLogger(__name__)


@dataclass
class RasterCovariate(BaseModel):
    """
    Represents a raster covariate layer derived from OSM or other sources.
    
    Attributes:
        name: Unique identifier for the covariate (e.g., 'building_density', 'tree_cover')
        description: Human-readable description
        source: Original data source (e.g., 'OSM', 'Sentinel-2')
        file_path: Path to the raster file
        crs: Coordinate Reference System
        resolution: Pixel resolution in meters
        nodata_value: Value representing no-data
        data_type: Data type (e.g., 'float32', 'uint8')
        min_value: Minimum value in the raster
        max_value: Maximum value in the raster
        mean_value: Mean value in the raster
        stats: Additional statistics
        metadata: Additional arbitrary metadata
    """
    name: str
    description: str
    source: str
    file_path: str
    crs: str
    resolution: float
    nodata_value: float = -9999.0
    data_type: str = "float32"
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mean_value: Optional[float] = None
    stats: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> bool:
        """Validate RasterCovariate schema."""
        if not self.name or not isinstance(self.name, str):
            logger.error("Covariate name must be a non-empty string")
            return False
        
        if not self.description:
            logger.error("Description is required")
            return False
        
        if not self.source:
            logger.error("Source is required")
            return False
        
        if not self.file_path:
            logger.error("File path is required")
            return False
        
        if not self.crs:
            logger.error("CRS is required")
            return False
        
        if self.resolution <= 0:
            logger.error("Resolution must be positive")
            return False
        
        if self.min_value is not None and self.max_value is not None:
            if self.min_value > self.max_value:
                logger.error("Min value cannot be greater than max value")
                return False
        
        return True

    def update_stats(self, min_val: float, max_val: float, mean_val: float) -> None:
        """Update statistical properties of the raster."""
        self.min_value = min_val
        self.max_value = max_val
        self.mean_value = mean_val
        logger.info(f"Updated stats for {self.name}: min={min_val}, max={max_val}, mean={mean_val}")
