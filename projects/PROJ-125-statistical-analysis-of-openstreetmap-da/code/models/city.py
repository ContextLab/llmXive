"""
CityBoundary model for managing city spatial extents.
"""
from typing import Optional, Dict, Any, List
from shapely.geometry import box, Polygon, mapping
from shapely.wkt import loads
import json
from pathlib import Path
import logging

from .base import BaseModel

logger = logging.getLogger(__name__)

class CityBoundary(BaseModel):
    """
    Represents a city boundary with metadata.
    
    Attributes:
        city_name: Name of the city.
        country: Country code or name.
        geometry_wkt: Well-Known Text representation of the geometry.
        crs_epsg: EPSG code of the coordinate reference system.
        source: Data source (e.g., 'OpenStreetMap', 'GADM').
        acquired_at: ISO timestamp of data acquisition.
    """
    
    REQUIRED_FIELDS = ["city_name", "geometry_wkt", "crs_epsg"]

    def __init__(
        self,
        city_name: str,
        geometry_wkt: str,
        crs_epsg: int,
        country: Optional[str] = None,
        source: Optional[str] = "OpenStreetMap",
        acquired_at: Optional[str] = None,
    ):
        """
        Initialize a CityBoundary instance.
        
        Args:
            city_name: Name of the city.
            geometry_wkt: WKT string of the polygon geometry.
            crs_epsg: EPSG code for the CRS.
            country: Optional country identifier.
            source: Optional data source string.
            acquired_at: Optional ISO timestamp.
        
        Raises:
            ValueError: If required fields are missing or invalid.
            Exception: If the WKT geometry is invalid.
        """
        # Validate inputs before assignment
        data = {
            "city_name": city_name,
            "geometry_wkt": geometry_wkt,
            "crs_epsg": crs_epsg,
            "country": country,
            "source": source,
            "acquired_at": acquired_at,
        }
        self.validate_schema(data, self.REQUIRED_FIELDS)

        # Validate WKT geometry
        try:
            self._geom = loads(geometry_wkt)
            if not self._geom.is_valid:
                raise ValueError(f"Invalid geometry WKT: {self._geom.wkt}")
        except Exception as e:
            raise ValueError(f"Failed to parse geometry WKT: {e}")

        self.city_name = city_name
        self.geometry_wkt = geometry_wkt
        self.crs_epsg = crs_epsg
        self.country = country
        self.source = source
        self.acquired_at = acquired_at

    @property
    def geometry(self):
        """Return the Shapely geometry object."""
        return self._geom

    @property
    def bounds(self) -> Dict[str, float]:
        """Return the bounding box as a dictionary."""
        minx, miny, maxx, maxy = self._geom.bounds
        return {
            "minx": minx,
            "miny": miny,
            "maxx": maxx,
            "maxy": maxy,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, ensuring geometry is WKT."""
        d = super().to_dict()
        # Ensure geometry is stored as WKT in the dict
        d["geometry_wkt"] = self.geometry_wkt
        return d

    @classmethod
    def from_geojson_file(cls, path: Path) -> "CityBoundary":
        """
        Load a CityBoundary from a GeoJSON file.
        
        Args:
            path: Path to the GeoJSON file.
        
        Returns:
            A CityBoundary instance.
        """
        path = Path(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Expect a Feature or a FeatureCollection with one feature
        if "features" in data:
            feature = data["features"][0]
        else:
            feature = data
        
        props = feature.get("properties", {})
        geom = feature.get("geometry", {})
        
        # Convert geometry to WKT
        wkt = mapping(geom) # This returns a dict, we need to reconstruct or use shapely directly
        # Actually, mapping returns a dict compatible with GeoJSON geometry. 
        # We need to convert that dict to a Shapely object then to WKT, or load WKT directly if available.
        # Since we have the dict, let's use shapely.geometry.shape
        from shapely.geometry import shape
        shapely_geom = shape(geom)
        wkt_str = shapely_geom.wkt

        city_name = props.get("name") or props.get("city_name") or "Unknown"
        country = props.get("country")
        source = props.get("source")
        acquired = props.get("acquired_at")
        crs = props.get("crs_epsg", 4326) # Default to WGS84 if not specified

        return cls(
            city_name=city_name,
            geometry_wkt=wkt_str,
            crs_epsg=crs,
            country=country,
            source=source,
            acquired_at=acquired,
        )
