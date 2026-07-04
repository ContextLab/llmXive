"""
CityBoundary model for storing administrative boundary data.
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
    Represents a city boundary with metadata.
    
    Attributes:
        city_name: Name of the city
        country: Country code or name
        crs: Coordinate Reference System (e.g., EPSG:4326)
        bounds: Bounding box [minx, miny, maxx, maxy]
        geometry_type: Type of geometry (e.g., 'Polygon', 'MultiPolygon')
        area_km2: Approximate area in square kilometers
        source: Data source (e.g., 'OpenStreetMap', 'GADM')
        metadata: Additional arbitrary metadata
    """
    city_name: str
    country: str
    crs: str = "EPSG:4326"
    bounds: Optional[List[float]] = None
    geometry_type: str = "Polygon"
    area_km2: Optional[float] = None
    source: str = "OpenStreetMap"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> bool:
        """Validate CityBoundary schema."""
        if not self.city_name or not isinstance(self.city_name, str):
            logger.error("City name must be a non-empty string")
            return False
        
        if not self.country or not isinstance(self.country, str):
            logger.error("Country must be a non-empty string")
            return False
        
        if self.bounds:
            if len(self.bounds) != 4:
                logger.error("Bounds must be a list of 4 floats [minx, miny, maxx, maxy]")
                return False
            if self.bounds[0] >= self.bounds[2] or self.bounds[1] >= self.bounds[3]:
                logger.error("Invalid bounds: min must be less than max")
                return False
        
        if not self.crs.startswith("EPSG:"):
            logger.warning(f"CRS format may be non-standard: {self.crs}")
        
        return True

    @classmethod
    def from_geojson(cls, geojson_data: Dict[str, Any]) -> "CityBoundary":
        """
        Create a CityBoundary from GeoJSON data.
        
        Args:
            geojson_data: GeoJSON Feature or FeatureCollection
        
        Returns:
            CityBoundary instance
        """
        if geojson_data.get("type") == "FeatureCollection":
            features = geojson_data.get("features", [])
            if not features:
                raise ValueError("Empty FeatureCollection")
            geojson_data = features[0]
        
        if geojson_data.get("type") != "Feature":
            raise ValueError("Expected GeoJSON Feature")
        
        props = geojson_data.get("properties", {})
        geometry = geojson_data.get("geometry", {})
        
        # Extract bounds from geometry if not in properties
        bounds = props.get("bounds")
        if not bounds and geometry.get("coordinates"):
            # Simple bounds calculation (assumes valid coordinates)
            coords = geometry["coordinates"]
            if geometry["type"] == "Polygon":
                coords = coords[0]
            elif geometry["type"] == "MultiPolygon":
                coords = [c for p in coords for c in p]
            
            if coords:
                lons = [c[0] for c in coords]
                lats = [c[1] for c in coords]
                bounds = [min(lons), min(lats), max(lons), max(lats)]
        
        # Try to infer city name from properties
        city_name = props.get("name") or props.get("name_en") or props.get("city")
        if not city_name:
            raise ValueError("Could not determine city name from GeoJSON")
        
        country = props.get("country") or props.get("iso_a2") or "Unknown"
        area = props.get("area_km2") or props.get("area")
        
        return cls(
            city_name=str(city_name),
            country=str(country),
            crs=props.get("crs", "EPSG:4326"),
            bounds=bounds,
            geometry_type=geometry.get("type", "Polygon"),
            area_km2=float(area) if area else None,
            source=props.get("source", "OpenStreetMap"),
            metadata={k: v for k, v in props.items() if k not in ["name", "name_en", "city", "country", "iso_a2", "area_km2", "area", "bounds", "crs", "source"]}
        )
