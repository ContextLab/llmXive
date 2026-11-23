"""
Schema definition for LEP Exclusion Data.

This module defines the data structures and validation logic for LEP
exclusion limits on dark matter parameters (mass vs coupling).
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
    Represents a single exclusion point from LEP data.

    Attributes:
        m_V (float): Vector mediator mass in MeV.
        g (float): Coupling constant (dimensionless).
        source (str): Reference string for the data point (e.g., 'LEP-II').
        comment (Optional[str]): Optional notes about the point.
    """
    m_V: float
    g: float
    source: str = "LEP-II"
    comment: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert dataclass to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LEPExclusionPoint':
        """Create instance from dictionary."""
        return cls(
            m_V=data['m_V'],
            g=data['g'],
            source=data.get('source', 'LEP-II'),
            comment=data.get('comment')
        )

    def validate(self) -> bool:
        """
        Validate the physical consistency of the point.

        Returns:
            bool: True if valid, False otherwise.
        """
        if not isinstance(self.m_V, (int, float)) or self.m_V <= 0:
            return False
        if not isinstance(self.g, (int, float)) or self.g <= 0:
            return False
        return True


@dataclass
class LEPExclusionData:
    """
    Container for a collection of LEP exclusion points.

    Attributes:
        points (List[LEPExclusionPoint]): List of exclusion data points.
        metadata (Dict[str, Any]): Metadata about the dataset (source, date, etc.).
    """
    points: List[LEPExclusionPoint] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_point(self, point: LEPExclusionPoint) -> None:
        """Add a single point to the dataset."""
        self.points.append(point)

    def add_points(self, points: List[LEPExclusionPoint]) -> None:
        """Add multiple points to the dataset."""
        self.points.extend(points)

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert the dataset to a pandas DataFrame.

        Returns:
            pd.DataFrame: DataFrame with columns ['m_V', 'g', 'source', 'comment'].
        """
        data = [p.to_dict() for p in self.points]
        return pd.DataFrame(data)

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame, metadata: Optional[Dict[str, Any]] = None) -> 'LEPExclusionData':
        """
        Create LEPExclusionData from a pandas DataFrame.

        Args:
            df: DataFrame with columns 'm_V' and 'g'.
            metadata: Optional metadata dictionary.

        Returns:
            LEPExclusionData: Instance populated from the DataFrame.
        """
        instance = cls(metadata=metadata or {})
        required_cols = ['m_V', 'g']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain columns: {required_cols}")

        for _, row in df.iterrows():
            point = LEPExclusionPoint(
                m_V=float(row['m_V']),
                g=float(row['g']),
                source=str(row.get('source', 'LEP-II')),
                comment=row.get('comment')
            )
            instance.add_point(point)
        return instance

    def to_json(self, filepath: Optional[Path] = None) -> Optional[str]:
        """
        Serialize the dataset to JSON.

        Args:
            filepath: Optional path to write the file. If None, returns string.

        Returns:
            Optional[str]: JSON string if filepath is None, else None.
        """
        data = {
            'metadata': self.metadata,
            'points': [p.to_dict() for p in self.points]
        }
        json_str = json.dumps(data, indent=2)
        if filepath:
            with open(filepath, 'w') as f:
                f.write(json_str)
            return None
        return json_str

    @classmethod
    def from_json(cls, filepath: Path) -> 'LEPExclusionData':
        """
        Load LEPExclusionData from a JSON file.

        Args:
            filepath: Path to the JSON file.

        Returns:
            LEPExclusionData: Loaded instance.
        """
        with open(filepath, 'r') as f:
            data = json.load(f)

        instance = cls(metadata=data.get('metadata', {}))
        for p_data in data.get('points', []):
            instance.add_point(LEPExclusionPoint.from_dict(p_data))
        return instance

    def validate_all(self) -> bool:
        """
        Validate all points in the dataset.

        Returns:
            bool: True if all points are valid, False otherwise.
        """
        return all(p.validate() for p in self.points)


def validate_lep_schema(data: LEPExclusionData) -> Dict[str, Any]:
    """
    Validate the LEP exclusion data schema and content.

    Args:
        data: The LEPExclusionData instance to validate.

    Returns:
        Dict[str, Any]: Validation report with 'valid' status and 'errors' list.
    """
    errors = []
    warnings = []

    # Check if data is empty
    if not data.points:
        warnings.append("Dataset contains no points.")

    # Validate metadata
    if not isinstance(data.metadata, dict):
        errors.append("Metadata must be a dictionary.")

    # Validate each point
    for i, point in enumerate(data.points):
        if not isinstance(point, LEPExclusionPoint):
            errors.append(f"Point {i} is not an LEPExclusionPoint instance.")
            continue

        if not point.validate():
            errors.append(f"Point {i} has invalid physical values (m_V={point.m_V}, g={point.g}).")

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'point_count': len(data.points)
    }
