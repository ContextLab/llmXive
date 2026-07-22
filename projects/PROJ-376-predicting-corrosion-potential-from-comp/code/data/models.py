"""
Base data model classes for the corrosion prediction pipeline.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import json


@dataclass
class AlloyRecord:
    """
    Represents a single alloy composition record.

    Attributes:
        alloy_id: Unique identifier for the alloy
        alloy_name: Human-readable name or designation
        specific_alloy_designation_id: Standard designation (e.g., UNS, ASTM)
        base_element: Primary metal element (e.g., 'Fe', 'Ni', 'Ti')
        weight_fractions: Dictionary of element -> weight fraction (0.0-1.0)
        heat_number: Batch/heat identification number
        manufacturer: Alloy manufacturer name
        notes: Additional notes or comments
        created_at: Timestamp of record creation
    """
    alloy_id: str
    alloy_name: Optional[str] = None
    specific_alloy_designation_id: Optional[str] = None
    base_element: Optional[str] = None
    weight_fractions: Dict[str, float] = field(default_factory=dict)
    heat_number: Optional[str] = None
    manufacturer: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary."""
        return {
            'alloy_id': self.alloy_id,
            'alloy_name': self.alloy_name,
            'specific_alloy_designation_id': self.specific_alloy_designation_id,
            'base_element': self.base_element,
            'weight_fractions': self.weight_fractions,
            'heat_number': self.heat_number,
            'manufacturer': self.manufacturer,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }

    def to_json(self) -> str:
        """Convert record to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class EnvironmentRecord:
    """
    Represents environmental conditions for a corrosion test.

    Attributes:
        env_id: Unique identifier for the environment record
        solution_type: Type of solution (e.g., 'NaCl', 'H2SO4')
        concentration: Concentration of solution (mol/L or wt%)
        ph: pH value of the solution
        temperature: Temperature in Celsius
        pressure: Pressure in atm (optional)
        aeration: Aeration status ('aerated', 'deaerated', 'unknown')
        flow_rate: Flow rate if applicable (m/s)
        reference_electrode: Reference electrode used
        notes: Additional notes
        created_at: Timestamp of record creation
    """
    env_id: str
    solution_type: Optional[str] = None
    concentration: Optional[float] = None
    ph: Optional[float] = None
    temperature: Optional[float] = None
    pressure: Optional[float] = None
    aeration: Optional[str] = None
    flow_rate: Optional[float] = None
    reference_electrode: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary."""
        return {
            'env_id': self.env_id,
            'solution_type': self.solution_type,
            'concentration': self.concentration,
            'ph': self.ph,
            'temperature': self.temperature,
            'pressure': self.pressure,
            'aeration': self.aeration,
            'flow_rate': self.flow_rate,
            'reference_electrode': self.reference_electrode,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }

    def to_json(self) -> str:
        """Convert record to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class CorrosionMeasurement:
    """
    Represents a corrosion measurement result.

    Attributes:
        measurement_id: Unique identifier for the measurement
        alloy_id: Reference to the alloy used
        env_id: Reference to the environment conditions
        corrosion_rate: Corrosion rate (mm/year or mpy)
        corrosion_potential: Corrosion potential (V vs reference)
        current_density: Current density (A/cm^2)
        test_duration: Duration of the test in hours
        test_method: Method used (e.g., 'potentiodynamic', 'weight_loss')
        standard: Standard followed (e.g., 'ASTM G59')
        uncertainty: Measurement uncertainty
        notes: Additional notes
        measured_at: Timestamp of measurement
    """
    measurement_id: str
    alloy_id: str
    env_id: str
    corrosion_rate: Optional[float] = None
    corrosion_potential: Optional[float] = None
    current_density: Optional[float] = None
    test_duration: Optional[float] = None
    test_method: Optional[str] = None
    standard: Optional[str] = None
    uncertainty: Optional[float] = None
    notes: Optional[str] = None
    measured_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary."""
        return {
            'measurement_id': self.measurement_id,
            'alloy_id': self.alloy_id,
            'env_id': self.env_id,
            'corrosion_rate': self.corrosion_rate,
            'corrosion_potential': self.corrosion_potential,
            'current_density': self.current_density,
            'test_duration': self.test_duration,
            'test_method': self.test_method,
            'standard': self.standard,
            'uncertainty': self.uncertainty,
            'notes': self.notes,
            'measured_at': self.measured_at.isoformat()
        }

    def to_json(self) -> str:
        """Convert record to JSON string."""
        return json.dumps(self.to_dict(), indent=2)