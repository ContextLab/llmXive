"""
Pydantic models for Biosynthetic Gene Cluster (BGC) features.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from enum import Enum

class BGCType(str, Enum):
    """
    Standardized BGC types based on antiSMASH/MIBiG classification.
    """
    PKS_I = "polyketide_type_I"
    PKS_II = "polyketide_type_II"
    PKS_III = "polyketide_type_III"
    NRPS = "non_ribosomal_peptide"
    NRPS_PKS = "hybrid_nrps_pks"
    RIPP = "ribose_incorporating_peptide"
    TERPENE = "terpene"
    SIDERO = "siderophore"
    BUTENOLIDE = "butenolide"
    LANTIBE = "lantibiotic"
    MICROCYSTIN = "microcystin"
    UNKNOWN = "unknown"

class BGCFeature(BaseModel):
    """
    Represents a single detected BGC feature within a genome.
    """
    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid"
    )

    feature_id: str = Field(..., description="Unique identifier for this BGC feature instance")
    species_id: str = Field(..., description="Reference to the parent species")
    bgc_type: BGCType = Field(..., description="Primary classification of the BGC")
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score from detection tool (e.g., antiSMASH)"
    )
    start_position: int = Field(..., ge=0, description="Genomic start coordinate (1-based)")
    end_position: int = Field(..., ge=0, description="Genomic end coordinate (1-based)")
    gene_count: Optional[int] = Field(None, ge=0, description="Number of genes in the cluster")
    known_cluster_match: Optional[str] = Field(None, description="MIBiG cluster ID if matched")
    detection_tool: str = Field("antismash", description="Tool used for detection")
    raw_attributes: Optional[dict] = Field(default_factory=dict, description="Raw JSON attributes from parser")
