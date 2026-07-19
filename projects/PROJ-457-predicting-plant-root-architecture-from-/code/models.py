from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class DataSourceType(Enum):
    """Enumeration of data source types to identify manipulated vs. natural conditions."""
    OBSERVATIONAL = "observational"
    MANIPULATED = "manipulated"
    CONTROLLED = "controlled"
    EXPERIMENTAL = "experimental"
    UNKNOWN = "unknown"

@dataclass
class RootPhenotypeRecord:
    """
    Represents a single record of root phenotype data.
    Corresponds to the structure expected from PlantPheno or RootReader datasets.
    """
    species: str
    root_length: Optional[float] = None
    branching_density: Optional[float] = None
    surface_area: Optional[float] = None
    diameter: Optional[float] = None
    total_root_mass: Optional[float] = None
    data_source: Optional[str] = None
    data_source_type: DataSourceType = DataSourceType.UNKNOWN
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None
    collection_date: Optional[datetime] = None
    study_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_valid_for_analysis(self, min_length: float = 0.0) -> bool:
        """
        Checks if the record has the minimum required fields for analysis.
        Per US1, we require non-null values for root metrics if they are predictors.
        """
        if not self.species:
            return False
        # Basic validity: at least one root metric present
        has_metric = any([
            self.root_length is not None,
            self.branching_density is not None,
            self.surface_area is not None
        ])
        return has_metric

@dataclass
class SoilNutrientRecord:
    """
    Represents soil nutrient data associated with a root phenotype record.
    Per Spec Deviation, we do not merge ISRIC; this record holds P/N data
    if present in the primary source or a direct merge.
    """
    phosphorus: Optional[float] = None  # mg/kg or ppm
    nitrogen: Optional[float] = None    # mg/kg or ppm
    potassium: Optional[float] = None   # mg/kg or ppm
    ph: Optional[float] = None
    organic_matter: Optional[float] = None
    texture_class: Optional[str] = None
    depth_cm: Optional[float] = None
    data_source: Optional[str] = None
    collection_date: Optional[datetime] = None

    def is_complete_for_analysis(self) -> bool:
        """
        Checks if critical nutrients (P and N) are present.
        Per US1 constraint: rows with missing P/N are excluded, not imputed.
        """
        return self.phosphorus is not None and self.nitrogen is not None

@dataclass
class MergedPhenotypeNutrientRecord:
    """
    Composite record combining RootPhenotypeRecord and SoilNutrientRecord.
    This is the primary unit of analysis for the modeling phase.
    """
    root: RootPhenotypeRecord
    soil: Optional[SoilNutrientRecord] = None
    
    @property
    def species(self) -> str:
        return self.root.species

    @property
    def has_nutrient_data(self) -> bool:
        return self.soil is not None and self.soil.is_complete_for_analysis()

    def to_dict(self) -> Dict[str, Any]:
        """Flattens the record into a dictionary suitable for DataFrame conversion."""
        base = {
            'species': self.root.species,
            'root_length': self.root.root_length,
            'branching_density': self.root.branching_density,
            'surface_area': self.root.surface_area,
            'diameter': self.root.diameter,
            'total_root_mass': self.root.total_root_mass,
            'data_source': self.root.data_source,
            'data_source_type': self.root.data_source_type.value,
            'location_lat': self.root.location_lat,
            'location_lon': self.root.location_lon,
            'study_id': self.root.study_id,
        }
        if self.soil:
            base.update({
                'phosphorus': self.soil.phosphorus,
                'nitrogen': self.soil.nitrogen,
                'potassium': self.soil.potassium,
                'ph': self.soil.ph,
                'organic_matter': self.soil.organic_matter,
                'texture_class': self.soil.texture_class,
                'depth_cm': self.soil.depth_cm,
            })
        return base