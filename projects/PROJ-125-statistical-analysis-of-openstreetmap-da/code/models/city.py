"""
CityBoundary model for representing administrative boundaries.
"""
from typing import Optional, Dict, Any, List
from shapely.geometry import box, Polygon, mapping
from shapely.wkt import loads
import json
from .base import BaseModel
from config import get_city_crs


class CityBoundary(BaseModel):
    """
    Represents the boundary of a city for spatial analysis.
    """

    def __init__(
        self,
        name: str,
        wkt_geometry: str,
        crs: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.crs = crs or get_city_crs()
        self.metadata = metadata or {}

        # Parse geometry
        try:
            self._geometry = loads(wkt_geometry)
        except Exception as e:
            raise ValueError(f"Invalid WKT geometry: {e}")

        # Validate geometry type
        if not isinstance(self._geometry, (Polygon, box)):
            raise ValueError(f"Geometry must be a Polygon or Box, got {type(self._geometry)}")

    @property
    def geometry(self):
        return self._geometry

    @property
    def bounds(self):
        return self._geometry.bounds

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "crs": self.crs,
            "geometry_wkt": self._geometry.wkt,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CityBoundary":
        return cls(
            name=data["name"],
            wkt_geometry=data["geometry_wkt"],
            crs=data.get("crs"),
            metadata=data.get("metadata", {}),
        )

    def validate(self) -> bool:
        """
        Validate the CityBoundary instance.
        Checks: name is not empty, geometry is valid, CRS is defined.
        """
        if not self.name or not isinstance(self.name, str):
            raise ValueError("City name must be a non-empty string")

        if not self._geometry.is_valid:
            raise ValueError("Geometry is not valid")

        if not self.crs:
            raise ValueError("CRS must be defined")

        return True

    def to_geojson(self) -> Dict[str, Any]:
        """
        Convert the boundary to a GeoJSON-like dictionary.
        """
        self.validate()
        return {
            "type": "Feature",
            "properties": {
                "name": self.name,
                "crs": self.crs,
                **self.metadata,
            },
            "geometry": mapping(self._geometry),
        }
