"""
Schema definitions for the Relic Lookup Table.

This module defines the data structures for pre-computed relic density
lookup tables used to accelerate the main scan pipeline. The tables
are generated using the Hulthen approximation for Sommerfeld enhancement
and stored in a structured format for fast interpolation.

Plan 1.2 Implementation: Define RelicLookupTable schema.
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
        m_dm: Dark matter particle mass in MeV.
        m_v: Vector mediator mass in MeV.
        g: Coupling constant (dimensionless).
        omega_dm_h2: Computed relic density parameter (Ω_dm * h^2).
        method: String identifier for the calculation method (e.g., 'Hulthen', 'Numerov').
        is_valid: Boolean flag indicating if the calculation converged successfully.
        error_estimate: Optional float for estimated numerical error.
        timestamp: Optional string for generation timestamp.
    """
    m_dm: float
    m_v: float
    g: float
    omega_dm_h2: float
    method: str = "Hulthen"
    is_valid: bool = True
    error_estimate: Optional[float] = None
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the entry to a dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RelicLookupTableEntry':
        """Create an entry from a dictionary."""
        return cls(**data)

    def validate(self) -> bool:
        """
        Validates the physical and numerical consistency of the entry.

        Returns:
            bool: True if the entry is valid, False otherwise.
        """
        # Physical constraints
        if self.m_dm <= 0 or self.m_v <= 0 or self.g <= 0:
            return False

        # Relic density must be non-negative
        if self.omega_dm_h2 < 0:
            return False

        # If marked invalid, it should not be used
        if not self.is_valid:
            return False

        return True


@dataclass
class RelicLookupTable:
    """
    Container for a complete Relic Lookup Table.

    This class manages a collection of RelicLookupTableEntry objects,
    providing methods for validation, serialization, and file I/O.

    Attributes:
        entries: List of lookup table entries.
        metadata: Dictionary for table metadata (generation date, parameters, etc.).
    """
    entries: List[RelicLookupTableEntry]
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        self.metadata.setdefault("version", "1.0")
        self.metadata.setdefault("entry_count", len(self.entries))

    def add_entry(self, entry: RelicLookupTableEntry):
        """Add a new entry to the table."""
        self.entries.append(entry)
        self.metadata["entry_count"] = len(self.entries)

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert the lookup table to a pandas DataFrame.

        Returns:
            pd.DataFrame: DataFrame containing all entries.
        """
        data = [entry.to_dict() for entry in self.entries]
        return pd.DataFrame(data)

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame, metadata: Optional[Dict[str, Any]] = None) -> 'RelicLookupTable':
        """
        Create a RelicLookupTable from a pandas DataFrame.

        Args:
            df: DataFrame with columns matching RelicLookupTableEntry fields.
            metadata: Optional metadata dictionary.

        Returns:
            RelicLookupTable: New instance.
        """
        entries = []
        for _, row in df.iterrows():
            entry_dict = row.to_dict()
            # Handle potential NaNs or None values gracefully
            if pd.isna(entry_dict.get('error_estimate')):
                entry_dict['error_estimate'] = None
            if pd.isna(entry_dict.get('timestamp')):
                entry_dict['timestamp'] = None
            entries.append(RelicLookupTableEntry(**entry_dict))
        
        return cls(entries=entries, metadata=metadata or {})

    def save_to_csv(self, filepath: str | Path):
        """
        Save the lookup table to a CSV file.

        Args:
            filepath: Path to the output CSV file.
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        df = self.to_dataframe()
        df.to_csv(path, index=False)

    @classmethod
    def load_from_csv(cls, filepath: str | Path) -> 'RelicLookupTable':
        """
        Load a lookup table from a CSV file.

        Args:
            filepath: Path to the input CSV file.

        Returns:
            RelicLookupTable: Loaded instance.
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Lookup table file not found: {path}")
        
        df = pd.read_csv(path)
        return cls.from_dataframe(df, metadata={"source_file": str(path)})

    def validate_all(self) -> bool:
        """
        Validate all entries in the table.

        Returns:
            bool: True if all entries are valid, False otherwise.
        """
        return all(entry.validate() for entry in self.entries)


def validate_entry(entry: RelicLookupTableEntry) -> bool:
    """
    Standalone function to validate a single entry.

    Args:
        entry: The entry to validate.

    Returns:
        bool: True if valid, False otherwise.
    """
    return entry.validate()


def validate_table(table: RelicLookupTable) -> bool:
    """
    Standalone function to validate an entire table.

    Args:
        table: The table to validate.

    Returns:
        bool: True if all entries are valid, False otherwise.
    """
    return table.validate_all()
