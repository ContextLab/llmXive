"""
Data model for Phenotype Records.

This module defines the schema for PhenotypeRecord, representing
sample-level metadata such as treatment conditions, temperature,
and time points.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum

class TreatmentType(Enum):
    """Enumeration of known treatment types."""
    CONTROL = "Control"
    HEAT_STRESS = "Heat Stress"
    COLD_STRESS = "Cold Stress"
    ACIDIFICATION = "Acidification"
    UNKNOWN = "Unknown"

@dataclass
class PhenotypeRecord:
    """
    Represents a single phenotype record for a sample.

    Attributes:
        sample_id (str): Unique identifier for the sample.
        treatment (TreatmentType): The treatment condition applied.
        temperature_celsius (Optional[float]): Recorded temperature during exposure.
        time_point_hours (Optional[float]): Duration of exposure in hours.
        metadata (Optional[Dict[str, Any]]): Additional arbitrary metadata.
    """
    sample_id: str
    treatment: TreatmentType
    temperature_celsius: Optional[float] = None
    time_point_hours: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate and normalize treatment type."""
        if isinstance(self.treatment, str):
            try:
                self.treatment = TreatmentType(self.treatment)
            except ValueError:
                self.treatment = TreatmentType.UNKNOWN

    @property
    def is_valid_for_analysis(self) -> bool:
        """
        Checks if the record has sufficient data for downstream analysis.
        Currently requires a valid sample_id and a non-Unknown treatment.
        """
        return self.treatment != TreatmentType.UNKNOWN and bool(self.sample_id)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the record to a dictionary for serialization."""
        return {
            "sample_id": self.sample_id,
            "treatment": self.treatment.value,
            "temperature_celsius": self.temperature_celsius,
            "time_point_hours": self.time_point_hours,
            "metadata": self.metadata
        }