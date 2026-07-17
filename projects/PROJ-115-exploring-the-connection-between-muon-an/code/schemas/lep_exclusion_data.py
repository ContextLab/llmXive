"""
Schema definition for LEP Exclusion Data.

This module defines the data structures and validation logic for LEP
exclusion limits on dark matter parameters (mass vs coupling).

Sources:
- Ref [2014]: LEP Limits on Dark Matter (ALEPH, DELPHI, L3, OPAL)
"""

from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any
import pandas as pd
from pathlib import Path
import math
import json


@dataclass
class LEPExclusionPoint:
    """
    Represents a single point on the LEP exclusion curve.
    
    Attributes:
        mass_mev: Dark matter particle mass in MeV.
        coupling_g: Dark photon coupling constant (dimensionless).
        limit_type: Type of limit (e.g., '95% CL', 'exclusion').
        source: Citation or experiment identifier (e.g., 'ALEPH', 'DELPHI').
        notes: Optional notes about the data point.
    """
    mass_mev: float
    coupling_g: float
    limit_type: str = "95% CL"
    source: str = "LEP Combined"
    notes: Optional[str] = None
    
    def __post_init__(self):
        """Validate physical constraints."""
        if self.mass_mev <= 0:
            raise ValueError(f"mass_mev must be positive, got {self.mass_mev}")
        if self.coupling_g <= 0:
            raise ValueError(f"coupling_g must be positive, got {self.coupling_g}")
        if not isinstance(self.mass_mev, (int, float)):
            raise TypeError(f"mass_mev must be numeric, got {type(self.mass_mev)}")
        if not isinstance(self.coupling_g, (int, float)):
            raise TypeError(f"coupling_g must be numeric, got {type(self.coupling_g)}")
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LEPExclusionPoint":
        """Create instance from dictionary."""
        return cls(
            mass_mev=data["mass_mev"],
            coupling_g=data["coupling_g"],
            limit_type=data.get("limit_type", "95% CL"),
            source=data.get("source", "LEP Combined"),
            notes=data.get("notes")
        )


@dataclass
class LEPExclusionData:
    """
    Container for the full LEP exclusion dataset.
    
    Attributes:
        points: List of exclusion curve points.
        metadata: Dictionary containing dataset metadata (source, date, version).
    """
    points: List[LEPExclusionPoint] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize default metadata if empty."""
        if not self.metadata:
            self.metadata = {
                "source": "LEP Experiments (ALEPH, DELPHI, L3, OPAL)",
                "reference": "Ref [2014]: LEP Limits on Dark Matter",
                "version": "1.0",
                "units": {
                    "mass": "MeV",
                    "coupling": "dimensionless"
                }
            }
            
    def add_point(self, point: LEPExclusionPoint) -> None:
        """Add a single exclusion point."""
        self.points.append(point)
        
    def add_points(self, points: List[LEPExclusionPoint]) -> None:
        """Add multiple exclusion points."""
        self.points.extend(points)
        
    def get_min_mass(self) -> Optional[float]:
        """Get the minimum mass in the dataset."""
        if not self.points:
            return None
        return min(p.mass_mev for p in self.points)
        
    def get_max_mass(self) -> Optional[float]:
        """Get the maximum mass in the dataset."""
        if not self.points:
            return None
        return max(p.mass_mev for p in self.points)
        
    def get_min_coupling(self) -> Optional[float]:
        """Get the minimum coupling in the dataset."""
        if not self.points:
            return None
        return min(p.coupling_g for p in self.points)
        
    def to_dataframe(self) -> pd.DataFrame:
        """Convert to pandas DataFrame."""
        data = [p.to_dict() for p in self.points]
        return pd.DataFrame(data)
        
    def to_json(self, path: Optional[Path] = None) -> Optional[str]:
        """Serialize to JSON string or write to file."""
        data = {
            "metadata": self.metadata,
            "points": [p.to_dict() for p in self.points]
        }
        json_str = json.dumps(data, indent=2)
        if path:
            with open(path, 'w') as f:
                f.write(json_str)
        return json_str
        
    @classmethod
    def from_json(cls, path: Path) -> "LEPExclusionData":
        """Load from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        
        points = [LEPExclusionPoint.from_dict(p) for p in data.get("points", [])]
        metadata = data.get("metadata", {})
        
        return cls(points=points, metadata=metadata)
        
    def to_parquet(self, path: Path) -> None:
        """Save to Parquet file."""
        df = self.to_dataframe()
        df.to_parquet(path, index=False)
        
    @classmethod
    def from_parquet(cls, path: Path) -> "LEPExclusionData":
        """Load from Parquet file."""
        df = pd.read_parquet(path)
        points = [
            LEPExclusionPoint(
                mass_mev=row['mass_mev'],
                coupling_g=row['coupling_g'],
                limit_type=row.get('limit_type', '95% CL'),
                source=row.get('source', 'LEP Combined'),
                notes=row.get('notes')
            )
            for _, row in df.iterrows()
        ]
        return cls(points=points)

def validate_lep_schema(data: LEPExclusionData) -> bool:
    """
    Validate the LEP exclusion data against schema requirements.
    
    Checks:
    - All points have valid mass and coupling values
    - No duplicate points
    - Data is sorted by mass
    - Metadata contains required fields
    
    Args:
        data: The LEPExclusionData instance to validate.
        
    Returns:
        True if valid, raises ValueError otherwise.
    """
    # Check points exist
    if not data.points:
        raise ValueError("LEPExclusionData must contain at least one point")
        
    # Check each point
    seen_points = set()
    prev_mass = -1.0
    
    for i, point in enumerate(data.points):
        # Validate individual point
        try:
            # Trigger post_init validation again
            point.__post_init__()
        except (ValueError, TypeError) as e:
            raise ValueError(f"Point {i} validation failed: {e}")
        
        # Check for duplicates
        key = (point.mass_mev, point.coupling_g)
        if key in seen_points:
            raise ValueError(f"Duplicate point found: {key}")
        seen_points.add(key)
        
        # Check sorting
        if point.mass_mev < prev_mass:
            raise ValueError(f"Points not sorted by mass at index {i}")
        prev_mass = point.mass_mev
        
    # Check metadata
    required_metadata = ["source", "reference"]
    for key in required_metadata:
        if key not in data.metadata:
            raise ValueError(f"Missing required metadata field: {key}")
            
    return True
