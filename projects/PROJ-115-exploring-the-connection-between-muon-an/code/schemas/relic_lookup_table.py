"""
Schema definitions for the RelicLookupTable data structure.

This module defines the Pydantic models used to validate and serialize
pre-computed relic density lookup tables used in the scan pipeline.
"""
import math
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import pandas as pd

# Using a lightweight dataclass for the core schema definition
# as Pydantic is not listed in the provided API surface dependencies.
# This ensures compatibility with the project's current stack.

@dataclass
class RelicLookupTableEntry:
    """
    Represents a single row in the pre-computed relic density lookup table.

    Attributes:
        m_dm_MeV: Dark matter mass in MeV.
        m_V_MeV: Vector mediator mass in MeV.
        g: Dark coupling constant (dimensionless).
        omega_dm_h2: Calculated relic density parameter (Omega_dm * h^2).
        is_resonant: Boolean flag indicating if the point is near a resonance (2*m_dm ~ m_V).
        approximation_error_pct: Estimated percentage error of the approximation method used.
    """
    m_dm_MeV: float
    m_V_MeV: float
    g: float
    omega_dm_h2: float
    is_resonant: bool = False
    approximation_error_pct: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert the entry to a dictionary."""
        return asdict(self)

@dataclass
class RelicLookupTable:
    """
    Container for the full RelicLookupTable dataset.

    This schema validates the structure of the lookup table data,
    ensuring it meets the requirements for the scan pipeline (Plan 1.2).

    Attributes:
        entries: List of RelicLookupTableEntry objects.
        metadata: Dictionary containing generation metadata (date, method, etc.).
    """
    entries: List[RelicLookupTableEntry]
    metadata: Dict[str, Any]

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert the lookup table to a pandas DataFrame for serialization.
        """
        data = [entry.to_dict() for entry in self.entries]
        return pd.DataFrame(data)

    def save_csv(self, path: str) -> None:
        """
        Save the lookup table to a CSV file.

        Args:
            path: File path to save the CSV.
        """
        df = self.to_dataframe()
        # Ensure directory exists
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)
        print(f"Saved RelicLookupTable to {path} with {len(self.entries)} entries.")

    @classmethod
    def load_csv(cls, path: str) -> "RelicLookupTable":
        """
        Load a lookup table from a CSV file.

        Args:
            path: File path to load from.

        Returns:
            RelicLookupTable instance.
        """
        if not Path(path).exists():
            raise FileNotFoundError(f"Lookup table file not found: {path}")

        df = pd.read_csv(path)
        entries = []
        for _, row in df.iterrows():
            entry = RelicLookupTableEntry(
                m_dm_MeV=float(row['m_dm_MeV']),
                m_V_MeV=float(row['m_V_MeV']),
                g=float(row['g']),
                omega_dm_h2=float(row['omega_dm_h2']),
                is_resonant=bool(row['is_resonant']),
                approximation_error_pct=float(row['approximation_error_pct'])
            )
            entries.append(entry)

        # Basic metadata reconstruction or default
        metadata = {
            "source_file": path,
            "row_count": len(entries)
        }

        return cls(entries=entries, metadata=metadata)

def validate_entry(entry: RelicLookupTableEntry) -> bool:
    """
    Validates a single entry for physical consistency.

    Returns:
        True if valid, False otherwise.
    """
    if entry.m_dm_MeV <= 0 or entry.m_V_MeV <= 0:
        return False
    if entry.g <= 0:
        return False
    if entry.omega_dm_h2 < 0:
        return False
    if not (0.0 <= entry.approximation_error_pct <= 100.0):
        return False
    return True

def validate_table(table: RelicLookupTable) -> bool:
    """
    Validates the entire lookup table.

    Returns:
        True if all entries are valid, False otherwise.
    """
    return all(validate_entry(e) for e in table.entries)
