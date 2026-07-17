"""
MicrobiomeProfile entity definition.
Represents the microbial composition for a participant at a specific time.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
import pandas as pd
import numpy as np

@dataclass
class MicrobiomeProfile:
    """
    Represents a microbiome profile (taxonomic counts or relative abundances).
    
    Attributes:
        participant_id: Link to the Participant entity.
        taxonomic_level: Level of taxonomy (e.g., 'Genus', 'Species').
        raw_counts: Dictionary mapping taxon names to raw read counts.
        zero_replaced_counts: Dictionary mapping taxon names to Bayesian-multiplicative replaced counts.
        clr_coordinates: Dictionary mapping taxon names to Centered Log-Ratio coordinates.
        ilr_coordinates: Dictionary mapping taxon names to Isometric Log-Ratio coordinates.
        total_reads: Total number of reads in the sample.
        sequencing_depth: Estimated sequencing depth.
        metadata: Additional sample metadata (e.g., extraction kit, batch).
    """
    participant_id: int
    taxonomic_level: str = "Genus"
    raw_counts: Dict[str, float] = field(default_factory=dict)
    zero_replaced_counts: Dict[str, float] = field(default_factory=dict)
    clr_coordinates: Dict[str, float] = field(default_factory=dict)
    ilr_coordinates: Dict[str, float] = field(default_factory=dict)
    total_reads: Optional[float] = None
    sequencing_depth: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_row(cls, row: pd.Series, taxon_columns: List[str]) -> "MicrobiomeProfile":
        """
        Create a MicrobiomeProfile from a pandas Series row.
        
        Args:
            row: The data row containing participant ID and taxon counts.
            taxon_columns: List of column names representing taxa.
        """
        participant_id = int(row.get("eid") or row.get("participant_id", 0))
        
        # Extract counts, handling NaNs as 0
        counts = {}
        total = 0.0
        for col in taxon_columns:
            val = row.get(col, 0.0)
            if pd.isna(val):
                val = 0.0
            counts[col] = float(val)
            total += float(val)
        
        profile = cls(
            participant_id=participant_id,
            raw_counts=counts,
            total_reads=total,
            sequencing_depth=total if total > 0 else None
        )
        return profile

    def add_zero_replaced(self, replaced_counts: Dict[str, float]) -> None:
        """Store the zero-replaced counts."""
        self.zero_replaced_counts = replaced_counts

    def add_clr(self, clr_coords: Dict[str, float]) -> None:
        """Store the CLR coordinates."""
        self.clr_coordinates = clr_coords

    def add_ilr(self, ilr_coords: Dict[str, float]) -> None:
        """Store the ILR coordinates."""
        self.ilr_coordinates = ilr_coords

    def to_dict(self) -> Dict[str, Any]:
        """Convert the profile to a dictionary."""
        return {
            "participant_id": self.participant_id,
            "taxonomic_level": self.taxonomic_level,
            "raw_counts": self.raw_counts,
            "zero_replaced_counts": self.zero_replaced_counts,
            "clr_coordinates": self.clr_coordinates,
            "ilr_coordinates": self.ilr_coordinates,
            "total_reads": self.total_reads,
            "sequencing_depth": self.sequencing_depth,
        }

    def get_ilr_dataframe(self) -> pd.DataFrame:
        """
        Convert ILR coordinates to a single-row DataFrame.
        """
        if not self.ilr_coordinates:
            raise ValueError("ILR coordinates not yet computed.")
        
        data = {
            "participant_id": self.participant_id,
            **self.ilr_coordinates
        }
        return pd.DataFrame([data])
