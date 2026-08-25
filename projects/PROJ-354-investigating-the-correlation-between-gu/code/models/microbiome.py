"""
MicrobiomeProfile entity definition.

Represents the gut microbiome composition for a participant at a specific time point.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
import pandas as pd
import numpy as np


@dataclass
class MicrobiomeProfile:
    """
    Represents a microbiome sample profile for a participant.

    Attributes:
        participant_id: Link to the participant.
        sample_id: Unique identifier for the specific sample.
        collection_date: Date the sample was collected.
        raw_counts: Dictionary mapping taxon (e.g., Genus name) to raw read counts.
        total_reads: Total number of reads in the sample.
        sequencing_platform: Platform used for sequencing (e.g., Illumina MiSeq).
        processing_pipeline: Bioinformatics pipeline version used.
        ilr_coordinates: Dictionary of ILR-transformed coordinates (if computed).
        zero_replaced_counts: Dictionary of counts after zero-replacement (if computed).
    """
    participant_id: int
    sample_id: str
    collection_date: Optional[str] = None
    raw_counts: Dict[str, int] = field(default_factory=dict)
    total_reads: Optional[int] = None
    sequencing_platform: Optional[str] = None
    processing_pipeline: Optional[str] = None
    ilr_coordinates: Dict[str, float] = field(default_factory=dict)
    zero_replaced_counts: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the profile to a dictionary, flattening counts if necessary."""
        base = {
            "participant_id": self.participant_id,
            "sample_id": self.sample_id,
            "collection_date": self.collection_date,
            "total_reads": self.total_reads,
            "sequencing_platform": self.sequencing_platform,
            "processing_pipeline": self.processing_pipeline,
        }

        # Flatten raw counts into columns: "count_TaxonName"
        for taxon, count in self.raw_counts.items():
            base[f"count_{taxon}"] = count

        # Flatten ILR coordinates
        for coord, val in self.ilr_coordinates.items():
            base[f"ilr_{coord}"] = val

        # Flatten zero-replaced counts
        for taxon, count in self.zero_replaced_counts.items():
            base[f"zc_count_{taxon}"] = count

        return base


def create_microbiome_dataframe(profiles: List[MicrobiomeProfile]) -> pd.DataFrame:
    """
    Convert a list of MicrobiomeProfile objects into a pandas DataFrame.

    Args:
        profiles: List of MicrobiomeProfile instances.

    Returns:
        A pandas DataFrame where rows are samples and columns are taxa/coordinates.
    """
    if not profiles:
        return pd.DataFrame()

    data = [p.to_dict() for p in profiles]
    df = pd.DataFrame(data)

    # Ensure numeric columns are numeric
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df
