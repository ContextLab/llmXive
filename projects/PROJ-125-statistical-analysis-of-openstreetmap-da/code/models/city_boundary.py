"""
CityBoundary model for storing and validating study area boundaries.

This model handles:
- WKT/Polygon geometry validation
- CRS identification and validation
- Bounding box calculations
- Metadata tracking (source, acquisition date)
"""
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
import json
from pathlib import Path
from .base import BaseModel
import logging

logger = logging.getLogger(__name__)


@dataclass
class CityBoundary(BaseModel):
    """
    Represents a city boundary for the study area.
    
    Attributes:
        city_name: Human-readable name of the city
        wkt_geometry: Well-Known Text representation of the boundary polygon
        crs_epsg: EPSG code of the coordinate reference system
        source: Data source (e.g., 'OpenStreetMap', 'GADM')
        acquisition_date: Date the boundary data was acquired
        bbox: Optional pre-calculated bounding box [minx, miny, maxx, maxy]
        metadata: Additional key-value metadata
    """
    city_name: str
    wkt_geometry: str
    crs_epsg: int
    source: str = "OpenStreetMap"
    acquisition_date: Optional[str] = None
    bbox: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate geometry and CRS after initialization."""
        self._validate_geometry()
        self._validate_crs()
        if self.bbox is None:
            self.bbox = self._calculate_bbox()

    def _validate_geometry(self) -> None:
        """Validate that WKT geometry is parseable and represents a valid polygon."""
        try:
            from shapely.wkt import loads
            geom = loads(self.wkt_geometry)
            if not geom.is_valid:
                logger.warning(f"Geometry for {self.city_name} is invalid: {geom.is_valid_reason}")
            if not geom.is_empty:
                if not geom.geom_type in ['Polygon', 'MultiPolygon']:
                    raise ValueError(f"Expected Polygon or MultiPolygon, got {geom.geom_type}")
        except ImportError:
            logger.warning("Shapely not installed, skipping geometry validation")
        except Exception as e:
            raise ValueError(f"Invalid WKT geometry: {e}")

    def _validate_crs(self) -> None:
        """Validate that CRS is a valid EPSG code."""
        if not isinstance(self.crs_epsg, int) or self.crs_epsg < 1:
            raise ValueError(f"Invalid EPSG code: {self.crs_epsg}")

    def _calculate_bbox(self) -> List[float]:
        """Calculate bounding box from WKT geometry."""
        try:
            from shapely.wkt import loads
            geom = loads(self.wkt_geometry)
            minx, miny, maxx, maxy = geom.bounds
            return [minx, miny, maxx, maxy]
        except ImportError:
            logger.warning("Shapely not installed, cannot calculate bbox")
            return [0.0, 0.0, 0.0, 0.0]
        except Exception as e:
            logger.error(f"Failed to calculate bbox: {e}")
            return [0.0, 0.0, 0.0, 0.0]

    def get_geometry_object(self):
        """Return Shapely geometry object if available."""
        try:
            from shapely.wkt import loads
            return loads(self.wkt_geometry)
        except ImportError:
            raise RuntimeError("Shapely required for geometry operations")

    @classmethod
    def _validate_required_fields(cls, data: Dict[str, Any]) -> None:
        """Validate required fields for CityBoundary."""
        required = ['city_name', 'wkt_geometry', 'crs_epsg']
        missing = [f for f in required if f not in data]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
