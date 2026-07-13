"""
Schema definition for the SpatialGridCell entity.

This module defines the Pydantic model for a single cell in the
spatial grid used for urban noise pollution analysis.
"""
from typing import Dict, Any, Optional
from datetime import date
from pydantic import BaseModel, Field, field_validator
from shapely.geometry import mapping, shape
from shapely.geometry.base import BaseGeometry


class SpatialGridCell(BaseModel):
    """
    Represents a single cell in the spatial grid for noise analysis.

    Attributes:
        grid_id: Unique identifier for the grid cell.
        geometry: The spatial geometry of the cell (Polygon, MultiPolygon, etc.).
        noise_metrics: Dictionary containing noise measurement statistics
                       (e.g., mean_db, max_db, percentile_95).
        covariates: Dictionary containing covariate data for the cell
                    (e.g., traffic_volume, population_density, land_use).
        date: The date associated with the measurements in this cell.
    """
    grid_id: str = Field(..., description="Unique identifier for the grid cell")
    geometry: BaseGeometry = Field(..., description="Shapely geometry object for the cell")
    noise_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Dictionary of noise metrics (e.g., mean, max, percentiles)"
    )
    covariates: Dict[str, float] = Field(
        default_factory=dict,
        description="Dictionary of covariate values (e.g., traffic, population)"
    )
    date: date = Field(..., description="Date of the measurement")

    @field_validator('geometry', mode='before')
    @classmethod
    def validate_geometry(cls, v):
        """
        Accepts either a Shapely geometry object or a GeoJSON-like dict.
        Converts GeoJSON-like dicts to Shapely geometry.
        """
        if isinstance(v, BaseGeometry):
            return v
        if isinstance(v, dict):
            return shape(v)
        raise TypeError(f"Expected Shapely geometry or GeoJSON dict, got {type(v)}")

    def to_geojson(self) -> Dict[str, Any]:
        """
        Converts the SpatialGridCell to a GeoJSON Feature dictionary.
        """
        return {
            "type": "Feature",
            "geometry": mapping(self.geometry),
            "properties": {
                "grid_id": self.grid_id,
                "noise_metrics": self.noise_metrics,
                "covariates": self.covariates,
                "date": self.date.isoformat()
            }
        }

    @classmethod
    def from_geojson_feature(cls, feature: Dict[str, Any]) -> 'SpatialGridCell':
        """
        Constructs a SpatialGridCell from a GeoJSON Feature dictionary.
        """
        props = feature.get("properties", {})
        date_str = props.get("date")
        if isinstance(date_str, str):
            date_obj = date.fromisoformat(date_str)
        else:
            date_obj = date_str

        return cls(
            grid_id=props.get("grid_id"),
            geometry=feature.get("geometry"),
            noise_metrics=props.get("noise_metrics", {}),
            covariates=props.get("covariates", {}),
            date=date_obj
        )