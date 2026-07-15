"""
Data models for the plant root architecture prediction pipeline.

Defines base data structures for root phenotype and soil nutrient records.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class RootPhenotypeRecord:
    """
    Represents a single root phenotype observation.

    Attributes:
        species (str): Scientific name of the plant species.
        root_length (float): Total root length (cm).
        branching_density (float): Number of branches per unit length.
        surface_area (float): Total root surface area (cm²).
        data_source (str): Source of the data (e.g., 'RootReader', 'PlantPheno').
        data_source_type (str): Type of data collection ('field', 'experimental', 'controlled').
        location_lat (Optional[float]): Latitude of collection site.
        location_lon (Optional[float]): Longitude of collection site.
        collection_date (Optional[datetime]): Date of collection.
        notes (Optional[str]): Additional metadata or notes.
        raw_data (Dict[str, Any]): Raw data dictionary for extended attributes.
    """
    species: str
    root_length: float
    branching_density: float
    surface_area: float
    data_source: str
    data_source_type: str
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None
    collection_date: Optional[datetime] = None
    notes: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to a dictionary, serializing datetime if present."""
        result = {
            'species': self.species,
            'root_length': self.root_length,
            'branching_density': self.branching_density,
            'surface_area': self.surface_area,
            'data_source': self.data_source,
            'data_source_type': self.data_source_type,
            'location_lat': self.location_lat,
            'location_lon': self.location_lon,
            'notes': self.notes,
        }
        if self.collection_date:
            result['collection_date'] = self.collection_date.isoformat()
        result.update(self.raw_data)
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RootPhenotypeRecord':
        """Create a RootPhenotypeRecord from a dictionary."""
        collection_date = None
        if 'collection_date' in data:
            try:
                collection_date = datetime.fromisoformat(data['collection_date'])
            except (ValueError, TypeError):
                collection_date = None
        
        # Extract known fields
        known_fields = {
            'species', 'root_length', 'branching_density', 'surface_area',
            'data_source', 'data_source_type', 'location_lat', 'location_lon',
            'collection_date', 'notes'
        }
        
        raw = {k: v for k, v in data.items() if k not in known_fields}
        
        return cls(
            species=data.get('species', ''),
            root_length=float(data.get('root_length', 0.0)),
            branching_density=float(data.get('branching_density', 0.0)),
            surface_area=float(data.get('surface_area', 0.0)),
            data_source=data.get('data_source', 'unknown'),
            data_source_type=data.get('data_source_type', 'unknown'),
            location_lat=data.get('location_lat'),
            location_lon=data.get('location_lon'),
            collection_date=collection_date,
            notes=data.get('notes'),
            raw_data=raw
        )


@dataclass
class SoilNutrientRecord:
    """
    Represents soil nutrient data for a specific location.

    Attributes:
        location_lat (float): Latitude of the soil sample.
        location_lon (float): Longitude of the soil sample.
        phosphorus (float): Phosphorus concentration (mg/kg).
        nitrogen (float): Nitrogen concentration (mg/kg).
        depth_cm (float): Soil sampling depth in cm.
        source (str): Source of the data (e.g., 'ISRIC').
        measurement_date (Optional[datetime]): Date of measurement.
        raw_data (Dict[str, Any]): Raw data dictionary for extended attributes.
    """
    location_lat: float
    location_lon: float
    phosphorus: float
    nitrogen: float
    depth_cm: float
    source: str
    measurement_date: Optional[datetime] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to a dictionary."""
        result = {
            'location_lat': self.location_lat,
            'location_lon': self.location_lon,
            'phosphorus': self.phosphorus,
            'nitrogen': self.nitrogen,
            'depth_cm': self.depth_cm,
            'source': self.source,
        }
        if self.measurement_date:
            result['measurement_date'] = self.measurement_date.isoformat()
        result.update(self.raw_data)
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SoilNutrientRecord':
        """Create a SoilNutrientRecord from a dictionary."""
        measurement_date = None
        if 'measurement_date' in data:
            try:
                measurement_date = datetime.fromisoformat(data['measurement_date'])
            except (ValueError, TypeError):
                measurement_date = None

        known_fields = {
            'location_lat', 'location_lon', 'phosphorus', 'nitrogen',
            'depth_cm', 'source', 'measurement_date'
        }

        raw = {k: v for k, v in data.items() if k not in known_fields}

        return cls(
            location_lat=float(data.get('location_lat', 0.0)),
            location_lon=float(data.get('location_lon', 0.0)),
            phosphorus=float(data.get('phosphorus', 0.0)),
            nitrogen=float(data.get('nitrogen', 0.0)),
            depth_cm=float(data.get('depth_cm', 0.0)),
            source=data.get('source', 'unknown'),
            measurement_date=measurement_date,
            raw_data=raw
        )