"""
Pydantic models for Biosynthetic Gene Clusters (BGCs).
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from enum import Enum

class BGCType(str, Enum):
    """
    Standard BGC types based on MIBiG/antiSMASH classification.
    """
    POLYKETIDE = "polyketide"
    NON_RIBOSOMAL_PEPTIDE = "non-ribosomal peptide"
    TERPENE = "terpene"
    ALKALOID = "alkaloid"
    RIBOSOMALLY_SYNTHESIZED = "ribosomally synthesized and post-translationally modified peptide"
    SACCHARIDE = "saccharide"
    OTHER = "other"
    UNKNOWN = "unknown"

class BGCFeature(BaseModel):
    """
    Represents a detected BGC feature in a genome.
    """
    model_config = ConfigDict(from_attributes=True)

    feature_id: str = Field(..., description="Unique feature identifier")
    species_id: str = Field(..., description="Reference to the species")
    bgc_type: BGCType = Field(..., description="Classification of the BGC")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Prediction confidence")
    start_position: int = Field(..., description="Genomic start coordinate")
    end_position: int = Field(..., description="Genomic end coordinate")
    gene_count: int = Field(..., description="Number of genes in the cluster")
    cluster_genes: Optional[List[str]] = Field(None, description="List of gene IDs in the cluster")
    detection_tool: Optional[str] = Field("antiSMASH", description="Tool used for detection")
    version: Optional[str] = Field(None, description="Tool version")
    raw_json_path: Optional[str] = Field(None, description="Path to raw antiSMASH JSON output")
