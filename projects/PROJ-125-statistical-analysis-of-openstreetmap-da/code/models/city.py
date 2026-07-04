"""
City Boundary model.
"""
from typing import Optional, Dict, Any
from shapely.geometry import box, Polygon, mapping
from shapely.wkt import loads
import json
from .base import BaseModel
from config import get_city_crs

class CityBoundary(BaseModel):
    """
    Represents a city boundary with CRS information.
    """
    
    def __init__(
        self,
        name: str,
        wkt: str,
        crs: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize CityBoundary.
        
        Args:
            name: City name
            wkt: Well-Known Text representation of the geometry
            crs: Coordinate Reference System string (e.g., EPSG:3857)
            metadata: Additional metadata dictionary
        """
        super().__init__()
        self.name = name
        self.wkt = wkt
        self.crs = crs or get_city_crs()
        self.metadata = metadata or {}
        
        # Parse geometry
        self.geometry = loads(wkt)
        
        # Validate geometry
        if not self.geometry.is_valid:
            raise ValueError(f"Invalid geometry for city {name}: {self.geometry.is_valid_reason}")
        
        if not isinstance(self.geometry, (Polygon, box)):
            raise ValueError(f"Geometry must be a Polygon or Box, got {type(self.geometry)}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with geometry as WKT."""
        return {
            "name": self.name,
            "wkt": self.wkt,
            "crs": self.crs,
            "metadata": self.metadata,
            "geom_type": self.geometry.geom_type
        }