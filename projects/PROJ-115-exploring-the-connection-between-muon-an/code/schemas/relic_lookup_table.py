"""
Schema definitions for the Relic Density Lookup Table.

This module defines the data structures for storing pre-computed relic density
values based on the Hulthen potential approximation (Sommerfeld enhancement).
These tables are used to accelerate the parameter scan by avoiding repeated
numerical integration.

Structure:
  - RelicLookupTableEntry: A single row in the lookup table.
  - RelicLookupTable: The container for all entries, with validation and I/O.
"""

import math
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np
import pandas as pd

@dataclass
class RelicLookupTableEntry:
    """
    Represents a single entry in the relic density lookup table.

    Attributes:
        m_dm_MeV: Dark matter mass in MeV.
        m_V_MeV: Vector mediator mass in MeV.
        g: Coupling constant (dimensionless).
        Omega_h2: Calculated relic density (Ωh²).
        regime: String flag indicating the physics regime:
                - "perturbative": Standard perturbative calculation.
                - "non-perturbative": Sommerfeld enhancement is significant.
                - "bound_state": Bound state formation effects included (if applicable).
                - "undefined": Parameters outside valid range.
        error_estimate: Optional float estimating numerical uncertainty (0.0 if exact).
    """
    m_dm_MeV: float
    m_V_MeV: float
    g: float
    Omega_h2: float
    regime: str = "perturbative"
    error_estimate: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert the entry to a dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RelicLookupTableEntry':
        """Create an entry from a dictionary."""
        return cls(**data)

@dataclass
class RelicLookupTable:
    """
    Container for the full relic density lookup table.

    Provides methods to validate the table structure, save to CSV/Parquet,
    and load from existing files.

    Attributes:
        entries: List of RelicLookupTableEntry objects.
        metadata: Dictionary for versioning, generation parameters, and provenance.
    """
    entries: List[RelicLookupTableEntry]
    metadata: Dict[str, Any]

    def validate(self) -> bool:
        """
        Validates the integrity of the lookup table.

        Checks:
          - No duplicate (m_dm, m_V, g) tuples.
          - All physical parameters are positive.
          - Omega_h2 is non-negative.
          - Regime is one of the allowed values.

        Returns:
            True if valid, raises ValueError otherwise.
        """
        seen_keys = set()
        allowed_regimes = {"perturbative", "non-perturbative", "bound_state", "undefined"}

        for i, entry in enumerate(self.entries):
            # Check for duplicates
            key = (entry.m_dm_MeV, entry.m_V_MeV, entry.g)
            if key in seen_keys:
                raise ValueError(f"Duplicate entry found at index {i}: {key}")
            seen_keys.add(key)

            # Physical constraints
            if entry.m_dm_MeV <= 0:
                raise ValueError(f"Invalid DM mass at index {i}: {entry.m_dm_MeV}")
            if entry.m_V_MeV <= 0:
                raise ValueError(f"Invalid Mediator mass at index {i}: {entry.m_V_MeV}")
            if entry.g <= 0:
                raise ValueError(f"Invalid coupling at index {i}: {entry.g}")
            if entry.Omega_h2 < 0:
                raise ValueError(f"Negative relic density at index {i}: {entry.Omega_h2}")
            if entry.regime not in allowed_regimes:
                raise ValueError(f"Invalid regime at index {i}: {entry.regime}")

        return True

    def to_dataframe(self) -> pd.DataFrame:
        """Convert the table to a pandas DataFrame."""
        data = [entry.to_dict() for entry in self.entries]
        return pd.DataFrame(data)

    def save_csv(self, filepath: Path) -> None:
        """
        Saves the lookup table to a CSV file.

        Args:
            filepath: Path to the output CSV file.
        """
        self.validate()
        df = self.to_dataframe()
        # Save metadata as comments or a separate JSON sidecar if needed
        # For now, standard CSV with headers
        df.to_csv(filepath, index=False)

    def save_parquet(self, filepath: Path) -> None:
        """
        Saves the lookup table to a Parquet file for efficient I/O.

        Args:
            filepath: Path to the output Parquet file.
        """
        self.validate()
        df = self.to_dataframe()
        df.to_parquet(filepath, index=False)

    @classmethod
    def load_csv(cls, filepath: Path) -> 'RelicLookupTable':
        """
        Loads a lookup table from a CSV file.

        Args:
            filepath: Path to the input CSV file.

        Returns:
            A RelicLookupTable instance.
        """
        if not filepath.exists():
            raise FileNotFoundError(f"Lookup table file not found: {filepath}")

        df = pd.read_csv(filepath)
        entries = []
        for _, row in df.iterrows():
            entry = RelicLookupTableEntry(
                m_dm_MeV=float(row['m_dm_MeV']),
                m_V_MeV=float(row['m_V_MeV']),
                g=float(row['g']),
                Omega_h2=float(row['Omega_h2']),
                regime=str(row['regime']),
                error_estimate=float(row.get('error_estimate', 0.0))
            )
            entries.append(entry)

        return cls(entries=entries, metadata={"source": str(filepath), "format": "csv"})

    @classmethod
    def load_parquet(cls, filepath: Path) -> 'RelicLookupTable':
        """
        Loads a lookup table from a Parquet file.

        Args:
            filepath: Path to the input Parquet file.

        Returns:
            A RelicLookupTable instance.
        """
        if not filepath.exists():
            raise FileNotFoundError(f"Lookup table file not found: {filepath}")

        df = pd.read_parquet(filepath)
        entries = []
        for _, row in df.iterrows():
            entry = RelicLookupTableEntry(
                m_dm_MeV=float(row['m_dm_MeV']),
                m_V_MeV=float(row['m_V_MeV']),
                g=float(row['g']),
                Omega_h2=float(row['Omega_h2']),
                regime=str(row['regime']),
                error_estimate=float(row.get('error_estimate', 0.0))
            )
            entries.append(entry)

        return cls(entries=entries, metadata={"source": str(filepath), "format": "parquet"})

def validate_entry(entry: RelicLookupTableEntry) -> bool:
    """
    Validates a single entry.

    Args:
        entry: The entry to validate.

    Returns:
        True if valid, raises ValueError otherwise.
    """
    if entry.m_dm_MeV <= 0 or entry.m_V_MeV <= 0 or entry.g <= 0:
        raise ValueError("Physical parameters must be positive.")
    if entry.Omega_h2 < 0:
        raise ValueError("Relic density must be non-negative.")
    return True

def validate_table(table: RelicLookupTable) -> bool:
    """
    Validates the entire table structure.

    Args:
        table: The table to validate.

    Returns:
        True if valid, raises ValueError otherwise.
    """
    return table.validate()