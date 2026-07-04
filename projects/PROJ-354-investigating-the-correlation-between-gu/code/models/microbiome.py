"""
MicrobiomeProfile entity definition.

Represents microbiome composition data for a participant, including
taxonomic counts and derived features.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
import pandas as pd
import numpy as np


@dataclass
class MicrobiomeProfile:
    """
    Represents the microbiome composition for a single participant.
    
    Attributes:
        participant_id: Link to the associated Participant.
        sample_date: Date of sample collection.
        sequencing_batch: Sequencing batch identifier.
        total_reads: Total number of reads in the sample.
        genus_counts: Dictionary mapping genus names to raw read counts.
        zero_replaced_counts: Dictionary mapping genus names to Bayesian-zero-replaced counts.
        clr_coordinates: Dictionary mapping genus names to Centered Log-Ratio transformed values.
        ilr_coordinates: Dictionary mapping ILR coordinate names to orthonormal coordinates.
        diversity_alpha: Optional alpha diversity metric (e.g., Shannon index).
        diversity_beta: Optional beta diversity metric if pre-computed.
        metadata: Additional sample metadata.
    """
    participant_id: int
    sample_date: Optional[str] = None
    sequencing_batch: Optional[str] = None
    total_reads: Optional[int] = None
    genus_counts: Dict[str, float] = field(default_factory=dict)
    zero_replaced_counts: Dict[str, float] = field(default_factory=dict)
    clr_coordinates: Dict[str, float] = field(default_factory=dict)
    ilr_coordinates: Dict[str, float] = field(default_factory=dict)
    diversity_alpha: Optional[float] = None
    diversity_beta: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary representation."""
        return {
            "participant_id": self.participant_id,
            "sample_date": self.sample_date,
            "sequencing_batch": self.sequencing_batch,
            "total_reads": self.total_reads,
            "genus_counts": self.genus_counts,
            "zero_replaced_counts": self.zero_replaced_counts,
            "clr_coordinates": self.clr_coordinates,
            "ilr_coordinates": self.ilr_coordinates,
            "diversity_alpha": self.diversity_alpha,
            "diversity_beta": self.diversity_beta,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_row(cls, row: pd.Series, count_columns: List[str]) -> "MicrobiomeProfile":
        """
        Create a MicrobiomeProfile from a pandas Series row.
        
        Args:
            row: A pandas Series containing microbiome data.
            count_columns: List of column names representing genus counts.
                
        Returns:
            A MicrobiomeProfile instance.
        """
        genus_counts = {}
        for col in count_columns:
            if col in row.index and pd.notna(row[col]):
                # Extract genus name from column name if needed (e.g., "genus_Bacteroides")
                genus_name = col.replace("genus_", "").replace("Genus_", "")
                genus_counts[genus_name] = float(row[col])
        
        return cls(
            participant_id=int(row["participant_id"]),
            sample_date=str(row["sample_date"]) if pd.notna(row.get("sample_date")) and row["sample_date"] != "" else None,
            sequencing_batch=str(row["sequencing_batch"]) if pd.notna(row.get("sequencing_batch")) and row["sequencing_batch"] != "" else None,
            total_reads=int(row["total_reads"]) if pd.notna(row.get("total_reads")) else None,
            genus_counts=genus_counts,
            metadata={}
        )
    
    def get_count_vector(self) -> np.ndarray:
        """Return genus counts as a numpy array."""
        if not self.genus_counts:
            return np.array([])
        return np.array(list(self.genus_counts.values()))
    
    def get_taxa_names(self) -> List[str]:
        """Return list of genus names in order."""
        return list(self.genus_counts.keys())
    
    def validate(self) -> List[str]:
        """
        Validate microbiome profile data integrity.
        
        Returns:
            A list of validation error messages. Empty if valid.
        """
        errors = []
        
        if self.participant_id is None or self.participant_id <= 0:
            errors.append("participant_id must be a positive integer")
        
        if self.total_reads is not None and self.total_reads <= 0:
            errors.append("total_reads must be positive")
        
        # Check for negative counts
        for genus, count in self.genus_counts.items():
            if count < 0:
                errors.append(f"Negative count for {genus}: {count}")
        
        # Check for zero-replaced counts consistency
        if self.zero_replaced_counts and len(self.zero_replaced_counts) != len(self.genus_counts):
            errors.append("Zero-replaced counts dimension mismatch")
        
        return errors
    
    def is_zero_replaced(self) -> bool:
        """Check if zero-replacement has been applied."""
        return bool(self.zero_replaced_counts)
    
    def is_clr_transformed(self) -> bool:
        """Check if CLR transformation has been applied."""
        return bool(self.clr_coordinates)
    
    def is_ilr_transformed(self) -> bool:
        """Check if ILR transformation has been applied."""
        return bool(self.ilr_coordinates)
