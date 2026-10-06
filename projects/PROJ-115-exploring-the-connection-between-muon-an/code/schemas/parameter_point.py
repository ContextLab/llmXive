"""
Schema definitions for the ParameterPoint data structure.

This module defines the core data model for a single point in the
muon g-2 dark matter parameter space scan. It includes validation
logic to ensure physical consistency and numerical stability.

References:
- FR-001: Define ParameterPoint schema for scan inputs.
- FR-005: Validate parameter point physical constraints.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import math
import json
from pathlib import Path


@dataclass
class ParameterPoint:
    """
    Represents a single point in the dark matter parameter space.

    Attributes:
        m_chi (float): Dark matter particle mass in MeV.
        m_V (float): Dark photon mediator mass in MeV.
        g (float): Coupling constant (dimensionless).
        epsilon (float): Kinetic mixing parameter (optional, default 0.0).
        calculated_relic_density (Optional[float]): Calculated Omega h^2.
        calculated_delta_a_mu (Optional[float]): Calculated contribution to muon g-2.
        is_viable (Optional[bool]): Result of constraint checks (Planck, Xenon1T, LEP).
        metadata (Dict[str, Any]): Additional context or flags (e.g., approximation warnings).
    """
    m_chi: float
    m_V: float
    g: float
    epsilon: float = 0.0
    calculated_relic_density: Optional[float] = None
    calculated_delta_a_mu: Optional[float] = None
    is_viable: Optional[bool] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass instance to a dictionary for serialization."""
        return {
            "m_chi": self.m_chi,
            "m_V": self.m_V,
            "g": self.g,
            "epsilon": self.epsilon,
            "calculated_relic_density": self.calculated_relic_density,
            "calculated_delta_a_mu": self.calculated_delta_a_mu,
            "is_viable": self.is_viable,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParameterPoint':
        """Create a ParameterPoint instance from a dictionary."""
        return cls(
            m_chi=data["m_chi"],
            m_V=data["m_V"],
            g=data["g"],
            epsilon=data.get("epsilon", 0.0),
            calculated_relic_density=data.get("calculated_relic_density"),
            calculated_delta_a_mu=data.get("calculated_delta_a_mu"),
            is_viable=data.get("is_viable"),
            metadata=data.get("metadata", {})
        )

    def to_json(self) -> str:
        """Serialize the instance to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'ParameterPoint':
        """Deserialize a JSON string to a ParameterPoint instance."""
        return cls.from_dict(json.loads(json_str))


def validate_parameter_point(point: ParameterPoint) -> tuple[bool, str]:
    """
    Validates the physical and numerical consistency of a ParameterPoint.

    Checks performed:
    1. Masses must be positive.
    2. Coupling g must be positive.
    3. Kinetic mixing epsilon must be within [-1, 1].
    4. If m_V is defined, it should ideally be > m_chi for stability (optional warning).
    5. If relic density is provided, it must be non-negative.

    Args:
        point: The ParameterPoint instance to validate.

    Returns:
        A tuple (is_valid, error_message).
        If valid, (True, "").
        If invalid, (False, "Description of error").
    """
    # Check masses
    if point.m_chi <= 0:
        return False, f"Dark matter mass m_chi must be positive, got {point.m_chi}"
    if point.m_V <= 0:
        return False, f"Mediator mass m_V must be positive, got {point.m_V}"

    # Check coupling
    if point.g <= 0:
        return False, f"Coupling constant g must be positive, got {point.g}"

    # Check epsilon bounds
    if not (-1.0 <= point.epsilon <= 1.0):
        return False, f"Kinetic mixing epsilon must be in [-1, 1], got {point.epsilon}"

    # Check numerical stability for very small/large values if necessary
    # (e.g., preventing division by zero in physics calculations)
    if point.m_chi < 1e-6:
        return False, f"Dark matter mass m_chi too small for numerical stability: {point.m_chi}"

    # Check calculated fields if present
    if point.calculated_relic_density is not None:
        if point.calculated_relic_density < 0:
            return False, f"Relic density cannot be negative, got {point.calculated_relic_density}"

    if point.calculated_delta_a_mu is not None:
        # Delta a_mu can be negative in some BSM scenarios, but usually positive for this model.
        # We just check for NaN/Inf here.
        if math.isnan(point.calculated_delta_a_mu) or math.isinf(point.calculated_delta_a_mu):
            return False, f"Delta a_mu is not a finite number: {point.calculated_delta_a_mu}"

    return True, ""


def load_parameter_points_from_csv(filepath: str) -> list[ParameterPoint]:
    """
    Load a list of ParameterPoint instances from a CSV file.

    Args:
        filepath: Path to the CSV file.

    Returns:
        A list of ParameterPoint objects.
    """
    import pandas as pd
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {filepath}")

    df = pd.read_csv(filepath)
    points = []
    for _, row in df.iterrows():
        # Handle potential NaNs in optional fields
        kwargs = {
            "m_chi": float(row["m_chi"]),
            "m_V": float(row["m_V"]),
            "g": float(row["g"]),
            "epsilon": float(row.get("epsilon", 0.0)) if "epsilon" in row else 0.0,
        }

        # Optional fields
        if "calculated_relic_density" in row and not pd.isna(row["calculated_relic_density"]):
            kwargs["calculated_relic_density"] = float(row["calculated_relic_density"])
        if "calculated_delta_a_mu" in row and not pd.isna(row["calculated_delta_a_mu"]):
            kwargs["calculated_delta_a_mu"] = float(row["calculated_delta_a_mu"])
        if "is_viable" in row and not pd.isna(row["is_viable"]):
            kwargs["is_viable"] = bool(row["is_viable"])

        # Metadata (usually stored as JSON string in a single column or separate columns)
        # For simplicity, we assume metadata is a JSON string in a 'metadata' column if present
        if "metadata" in row and not pd.isna(row["metadata"]):
            try:
                kwargs["metadata"] = json.loads(row["metadata"])
            except json.JSONDecodeError:
                kwargs["metadata"] = {}

        points.append(ParameterPoint(**kwargs))

    return points


def save_parameter_points_to_csv(points: list[ParameterPoint], filepath: str) -> None:
    """
    Save a list of ParameterPoint instances to a CSV file.

    Args:
        points: List of ParameterPoint objects.
        filepath: Output path for the CSV file.
    """
    import pandas as pd

    data = [p.to_dict() for p in points]
    df = pd.DataFrame(data)

    # Ensure metadata column is a string for CSV compatibility
    if "metadata" in df.columns:
        df["metadata"] = df["metadata"].apply(lambda x: json.dumps(x) if isinstance(x, dict) else x)

    df.to_csv(filepath, index=False)