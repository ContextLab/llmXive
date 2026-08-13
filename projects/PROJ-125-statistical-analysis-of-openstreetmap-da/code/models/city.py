"""
CityBoundary model for handling urban area definitions.
"""
from typing import Optional, Dict, Any, List
from shapely.geometry import box, Polygon, mapping
from shapely.wkt import loads
import json
from .base import BaseModel
from config import get_city_crs
import logging

logger = logging.getLogger(__name__)


class CityBoundary(BaseModel):
    """
    Represents a city boundary with metadata.
    
    Attributes:
        city_name: Name of the city.
        geometry: Shapely geometry object (Polygon or MultiPolygon).
        crs: Coordinate Reference System (EPSG code or string).
        source: Source of the boundary data (e.g., 'osm', 'gadm').
        metadata: Additional arbitrary metadata.
    """

    def __init__(
        self,
        city_name: str,
        geometry: Any,
        crs: Optional[str] = None,
        source: str = "osm",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.city_name = city_name
        self.crs = crs or get_city_crs(city_name)
        self.source = source
        self.metadata = metadata or {}
        
        # Handle geometry serialization/deserialization
        if isinstance(geometry, str):
            self.geometry = loads(geometry)
        elif isinstance(geometry, dict) and "type" in geometry:
            # GeoJSON dict
            self.geometry = loads(json.dumps(geometry))
        else:
            self.geometry = geometry

    def validate(self) -> bool:
        """
        Validate the CityBoundary instance.
        
        Checks:
        1. City name is not empty.
        2. Geometry is valid.
        3. CRS is defined.
        """
        if not self.city_name or not isinstance(self.city_name, str):
            logger.error("City name must be a non-empty string.")
            return False

        if self.geometry is None:
            logger.error("Geometry cannot be None.")
            return False

        if not self.geometry.is_valid:
            logger.error(f"Geometry is invalid: {self.geometry.is_valid_reason}")
            return False

        if not self.crs:
            logger.error("CRS is not defined.")
            return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the CityBoundary to a dictionary (GeoJSON compatible).
        """
        return {
            "type": "Feature",
            "properties": {
                "city_name": self.city_name,
                "source": self.source,
                "metadata": self.metadata,
            },
            "geometry": mapping(self.geometry),
            "crs": {"type": "name", "properties": {"name": self.crs}},
        }

    def get_bounds(self) -> tuple:
        """
        Return the bounding box (minx, miny, maxx, maxy).
        """
        return self.geometry.bounds

    @classmethod
    def from_geojson(cls, geojson_path: str) -> "CityBoundary":
        """
        Load a CityBoundary from a GeoJSON file.
        Expects a FeatureCollection or a single Feature.
        """
        with open(geojson_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if data.get("type") == "FeatureCollection":
            if len(data["features"]) == 0:
                raise ValueError("GeoJSON FeatureCollection is empty.")
            feature = data["features"][0]
        elif data.get("type") == "Feature":
            feature = data
        else:
            raise ValueError("Invalid GeoJSON structure.")

        props = feature.get("properties", {})
        city_name = props.get("city_name", "Unknown")
        geometry = feature.get("geometry")
        crs = data.get("crs", {}).get("properties", {}).get("name", "EPSG:4326")

        return cls(city_name=city_name, geometry=geometry, crs=crs, source="file")
