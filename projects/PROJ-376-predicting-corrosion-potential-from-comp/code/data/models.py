"""
Data model classes for the corrosion prediction pipeline.

Defines the core data structures for Alloy compositions,
Environmental conditions, and Corrosion measurements.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
from utils.exceptions import DataInsufficientError
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AlloyRecord:
    """
    Represents a specific alloy composition.

    Attributes:
        alloy_id: Unique identifier for the alloy record.
        specific_alloy_designation_id: The specific alloy designation (e.,g., '304 Stainless Steel').
        base_element: The primary base metal (e.g., 'Fe', 'Ni', 'Ti').
        weight_fractions: Dictionary of element name to weight fraction (0.0-1.0).
        source: Origin of the data (e.g., 'NIST-IR-8200').
        timestamp: Timestamp of record creation or ingestion.
    """
    alloy_id: str
    specific_alloy_designation_id: str
    base_element: str
    weight_fractions: Dict[str, float]
    source: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def validate(self) -> None:
        """
        Validates the integrity of the alloy record.
        Raises DataInsufficientError if critical fields are missing or invalid.
        """
        if not self.alloy_id:
            raise DataInsufficientError("AlloyRecord missing 'alloy_id'")
        if not self.specific_alloy_designation_id:
            raise DataInsufficientError("AlloyRecord missing 'specific_alloy_designation_id'")
        if not self.base_element:
            raise DataInsufficientError("AlloyRecord missing 'base_element'")
        
        # Validate weight fractions
        if not self.weight_fractions:
            raise DataInsufficientError("AlloyRecord missing 'weight_fractions'")
        
        total_fraction = sum(self.weight_fractions.values())
        if not (0.99 <= total_fraction <= 1.01):
            logger.warning(
                f"Alloy {self.alloy_id} weight fractions sum to {total_fraction:.4f} "
                f"(expected ~1.0). This may indicate data quality issues."
            )

    def to_dict(self) -> Dict[str, Any]:
        """Converts the record to a dictionary for serialization."""
        return {
            "alloy_id": self.alloy_id,
            "specific_alloy_designation_id": self.specific_alloy_designation_id,
            "base_element": self.base_element,
            "weight_fractions": self.weight_fractions,
            "source": self.source,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlloyRecord":
        """Creates an AlloyRecord from a dictionary."""
        ts = data.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        return cls(
            alloy_id=data["alloy_id"],
            specific_alloy_designation_id=data["specific_alloy_designation_id"],
            base_element=data["base_element"],
            weight_fractions=data["weight_fractions"],
            source=data.get("source"),
            timestamp=ts
        )


@dataclass
class EnvironmentRecord:
    """
    Represents the environmental conditions of a corrosion test.

    Attributes:
        env_id: Unique identifier for the environment record.
        pH: The pH of the solution.
        temperature: Temperature in Celsius.
        electrolyte_type: Type of electrolyte (e.g., 'NaCl', 'H2SO4').
        concentration: Concentration of the electrolyte (e.g., in mol/L or %).
        dissolved_oxygen: Dissolved oxygen level (optional, mg/L).
        flow_rate: Flow rate of the solution (optional, m/s).
        timestamp: Timestamp of the measurement.
    """
    env_id: str
    pH: float
    temperature: float
    electrolyte_type: str
    concentration: Optional[float] = None
    dissolved_oxygen: Optional[float] = None
    flow_rate: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def validate(self) -> None:
        """
        Validates the integrity of the environment record.
        Raises DataInsufficientError if critical fields are missing or invalid.
        """
        if not self.env_id:
            raise DataInsufficientError("EnvironmentRecord missing 'env_id'")
        
        # pH validation (typically 0-14, but allow slight outliers for logging)
        if not (0.0 <= self.pH <= 14.0):
            logger.warning(f"Environment {self.env_id} has pH {self.pH} outside typical range [0, 14].")
        
        # Temperature validation (usually > 0 for aqueous solutions)
        if self.temperature <= 0:
            logger.warning(f"Environment {self.env_id} has temperature {self.temperature} <= 0°C.")

    def to_dict(self) -> Dict[str, Any]:
        """Converts the record to a dictionary for serialization."""
        return {
            "env_id": self.env_id,
            "pH": self.pH,
            "temperature": self.temperature,
            "electrolyte_type": self.electrolyte_type,
            "concentration": self.concentration,
            "dissolved_oxygen": self.dissolved_oxygen,
            "flow_rate": self.flow_rate,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnvironmentRecord":
        """Creates an EnvironmentRecord from a dictionary."""
        ts = data.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        return cls(
            env_id=data["env_id"],
            pH=data["pH"],
            temperature=data["temperature"],
            electrolyte_type=data["electrolyte_type"],
            concentration=data.get("concentration"),
            dissolved_oxygen=data.get("dissolved_oxygen"),
            flow_rate=data.get("flow_rate"),
            timestamp=ts
        )


@dataclass
class CorrosionMeasurement:
    """
    Represents a measured corrosion potential resulting from an alloy-environment pair.

    Attributes:
        measurement_id: Unique identifier for the measurement.
        alloy_id: Reference to the AlloyRecord.
        env_id: Reference to the EnvironmentRecord.
        corrosion_potential: Measured potential in millivolts (mV).
        measurement_method: Method used (e.g., 'OCP', 'Potentiodynamic').
        duration: Duration of the measurement in seconds.
        timestamp: Timestamp of the measurement.
    """
    measurement_id: str
    alloy_id: str
    env_id: str
    corrosion_potential: float
    measurement_method: Optional[str] = None
    duration: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def validate(self) -> None:
        """
        Validates the integrity of the measurement record.
        Raises DataInsufficientError if critical fields are missing.
        """
        if not self.measurement_id:
            raise DataInsufficientError("CorrosionMeasurement missing 'measurement_id'")
        if not self.alloy_id:
            raise DataInsufficientError("CorrosionMeasurement missing 'alloy_id'")
        if not self.env_id:
            raise DataInsufficientError("CorrosionMeasurement missing 'env_id'")
        
        # Corrosion potential is typically negative for active corrosion, but can be positive.
        # We only check that it's a valid number.
        if not isinstance(self.corrosion_potential, (int, float)):
            raise DataInsufficientError(f"CorrosionMeasurement has invalid potential type: {type(self.corrosion_potential)}")

    def to_dict(self) -> Dict[str, Any]:
        """Converts the record to a dictionary for serialization."""
        return {
            "measurement_id": self.measurement_id,
            "alloy_id": self.alloy_id,
            "env_id": self.env_id,
            "corrosion_potential": self.corrosion_potential,
            "measurement_method": self.measurement_method,
            "duration": self.duration,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CorrosionMeasurement":
        """Creates a CorrosionMeasurement from a dictionary."""
        ts = data.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        return cls(
            measurement_id=data["measurement_id"],
            alloy_id=data["alloy_id"],
            env_id=data["env_id"],
            corrosion_potential=data["corrosion_potential"],
            measurement_method=data.get("measurement_method"),
            duration=data.get("duration"),
            timestamp=ts
        )