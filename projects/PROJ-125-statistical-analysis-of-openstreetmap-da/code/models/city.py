"""
City boundary model for OSM data ingestion.
"""
from typing import Optional, Dict, Any
from shapely.geometry import box, Polygon, mapping
from shapely.wkt import loads
import json
from .base import BaseModel
from config import get_city_crs


class CityBoundary(BaseModel):
    """
    Represents a city boundary with associated metadata.
    
    Attributes:
        city_name: Name of the city
        country: Country code or name
        geometry: WKT string representation of the boundary polygon
        epsg_code: EPSG code for the coordinate reference system
        area_km2: Calculated area in square kilometers (optional)
        source: Data source (e.g., 'OSM', 'Natural Earth')
    """
    
    REQUIRED_FIELDS = ["city_name", "country", "geometry"]

    def __init__(
        self,
        city_name: str,
        country: str,
        geometry: str,
        epsg_code: int = 4326,
        area_km2: Optional[float] = None,
        source: str = "OSM",
    ):
        """
        Initialize a CityBoundary instance.
        
        Args:
            city_name: Name of the city
            country: Country code or name
            geometry: WKT string representation of the boundary polygon
            epsg_code: EPSG code for the CRS
            area_km2: Pre-calculated area in km²
            source: Data source identifier
        """
        self.city_name = city_name
        self.country = country
        self.geometry = geometry
        self.epsg_code = epsg_code
        self.area_km2 = area_km2
        self.source = source

        # Validate schema on init
        self.validate_schema(
            self.to_dict(), 
            self.REQUIRED_FIELDS
        )

    @property
    def shapely_geom(self) -> Polygon:
        """Return the geometry as a Shapely Polygon object."""
        return loads(self.geometry)

    @property
    def bbox(self) -> tuple:
        """Return the bounding box (minx, miny, maxx, maxy)."""
        return self.shapely_geom.bounds

    def to_wkt(self) -> str:
        """Return the geometry as a WKT string."""
        return self.geometry

    def to_geojson(self) -> Dict[str, Any]:
        """Convert to GeoJSON Feature dictionary."""
        return {
            "type": "Feature",
            "properties": {
                "city_name": self.city_name,
                "country": self.country,
                "epsg_code": self.epsg_code,
                "area_km2": self.area_km2,
                "source": self.source,
            },
            "geometry": mapping(self.shapely_geom),
        }

    def get_crs(self) -> int:
        """Get the EPSG code for the coordinate reference system."""
        return self.epsg_code

    @classmethod
    def from_osm_query(cls, city_name: str, country: str, wkt: str) -> "CityBoundary":
        """
        Factory method to create CityBoundary from OSM query results.
        
        Args:
            city_name: Name of the city
            country: Country code or name
            wkt: WKT geometry string from OSM
            
        Returns:
            CityBoundary instance
        """
        # Calculate area if possible
        geom = loads(wkt)
        area_km2 = None
        if geom.area > 0:
            # Assume input is in degrees (EPSG:4326), convert roughly
            # For precise area, reprojection would be needed, but this is a proxy
            bbox = geom.bounds
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            # Approximate conversion: 1 deg ~ 111 km at equator
            area_km2 = width * height * 111 * 111 * 0.7 # Rough adjustment for mid-latitudes
        
        return cls(
            city_name=city_name,
            country=country,
            geometry=wkt,
            epsg_code=4326,
            area_km2=area_km2,
            source="OSM"
        )
