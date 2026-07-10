"""
Pydantic model for Biosynthetic Gene Cluster (BGC) features.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from enum import Enum

class BGCType(str, Enum):
    """Standardized BGC types based on antiSMASH/MIBiG classification."""
    PKS_I = "PKS_I"
    PKS_II = "PKS_II"
    PKS_III = "PKS_III"
    NRPS = "NRPS"
    RiPP = "RiPP"
    Terpenoid = "Terpenoid"
    Alkaloid = "Alkaloid"
    Phenol = "Phenol"
    Others = "Others"

class BGCFeature(BaseModel):
    """
    Represents a detected Biosynthetic Gene Cluster.

    Attributes:
        bgc_id: Unique identifier for the BGC instance.
        species_id: Foreign key to the Species model.
        cluster_type: The type of BGC (PKS, NRPS, etc.).
        confidence_score: Detection confidence score from antiSMASH (0.0 - 1.0).
        start_pos: Start position on the contig/chromosome.
        end_pos: End position on the contig/chromosome.
        contig_id: Identifier of the contig/chromosome containing the BGC.
        mibig_match_id: Optional MIBiG reference ID if matched.
        mibig_similarity: Optional similarity score to the MIBiG match.
    """
    model_config = ConfigDict(from_attributes=True)

    bgc_id: str = Field(..., description="Unique BGC identifier")
    species_id: str = Field(..., description="Associated species ID")
    cluster_type: BGCType = Field(..., description="Type of biosynthetic cluster")
    confidence_score: float = Field(..., description="Detection confidence", ge=0.0, le=1.0)
    start_pos: int = Field(..., description="Start position", gt=0)
    end_pos: int = Field(..., description="End position", gt=0)
    contig_id: str = Field(..., description="Contig/Chromosome ID")
    mibig_match_id: Optional[str] = Field(None, description="MIBiG match ID")
    mibig_similarity: Optional[float] = Field(None, description="MIBiG similarity score", ge=0.0, le=1.0)

    def is_high_confidence(self, threshold: float = 0.7) -> bool:
        """Check if the BGC detection meets the confidence threshold."""
        return self.confidence_score >= threshold
