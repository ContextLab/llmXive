"""
Base data schemas for the plant defense allocation pipeline.

These Pydantic models are defined inline based on FR-001, FR-006, and FR-017.
They serve as the contract for data validation throughout the pipeline.
"""
from datetime import datetime
from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
import hashlib
import json
import os


class RNASeqStudy(BaseModel):
    """
    Represents an RNA-seq study metadata entry.
    Derived from FR-001 (Data Acquisition).
    """
    accession_id: str = Field(..., description="Unique identifier for the study (e.g., SRA or GEO accession)")
    species: str = Field(..., description="Scientific name of the plant species")
    tissue: str = Field(..., description="Tissue type sampled (e.g., leaf, root)")
    treatment: str = Field(..., description="Treatment condition (e.g., herbivore attack, control)")
    replicates: int = Field(..., ge=1, description="Number of biological replicates")


class HerbivoreResponseVector(BaseModel):
    """
    Represents a vector of gene responses to herbivory.
    Derived from FR-006 (Differential Expression).
    """
    gene_id: str = Field(..., description="Identifier for the gene")
    log2fc: float = Field(..., description="Log2 fold change relative to control")
    pvalue: float = Field(..., ge=0.0, le=1.0, description="Statistical p-value")
    herbivore_type: str = Field(..., description="Type of herbivore used in the experiment")


class DefenseAllocationIndex(BaseModel):
    """
    Represents the calculated Defense Allocation Index for a species.
    Derived from FR-006 (Trait Compilation).
    """
    species: str = Field(..., description="Scientific name of the species")
    chemical_mean: float = Field(..., description="Mean standardized chemical defense trait value")
    physical_mean: float = Field(..., description="Mean standardized physical defense trait value")
    ratio: float = Field(..., description="Ratio of chemical to physical defense (DAI)")


class Species(BaseModel):
    """
    Represents a species with its associated biological context.
    Derived from FR-017 (Phylogenetic Context).
    """
    name: str = Field(..., description="Scientific name of the species")
    tissue_types: List[str] = Field(default_factory=list, description="List of tissue types available for this species")
    herbivore_types: List[str] = Field(default_factory=list, description="List of herbivore types tested for this species")


class ProvenanceInfo(BaseModel):
    """Provenance metadata for data artifacts."""
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    tool_versions: Dict[str, str] = Field(default_factory=dict)
    source_accession: Optional[str] = None
    checksum: Optional[str] = None

class ManifestEntry(BaseModel):
    """Entry in a data manifest."""
    file_name: str
    checksum: str
    source_type: Literal["real", "synthetic"]
    accession_id: str
    organism: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DataManifest(BaseModel):
    """Container for a list of manifest entries."""
    entries: List[ManifestEntry]
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class ExpressionMatrixMetadata(BaseModel):
    """Metadata for an expression matrix."""
    accession_id: str
    species: str
    tissue: str
    treatment: str
    gene_count: int
    sample_count: int
    normalization_method: str = "TPM"

class ExpressionMatrix(BaseModel):
    """
    Container for an expression matrix and its metadata.
    Note: The matrix data itself is stored in pandas DataFrames in memory or CSV/Parquet on disk.
    This schema validates the metadata structure.
    """
    metadata: ExpressionMatrixMetadata
    # The actual matrix is handled by pandas/numpy in the processing scripts
    # This schema ensures the metadata adheres to the contract

class DefenseTrait(BaseModel):
    """Single defense trait measurement."""
    species_name: str
    trait_name: str
    trait_value: float
    unit: str
    source_id: str

class TraitDataset(BaseModel):
    """Collection of defense traits for a species or study."""
    species: str
    traits: List[DefenseTrait]
    source: str

class DEGResult(BaseModel):
    """Result of a Differential Expression analysis for a single gene."""
    gene_id: str
    log2fc: float
    pvalue: float
    adj_pvalue: Optional[float] = None
    base_mean: float

class DEGAnalysisResult(BaseModel):
    """Full result of a Differential Expression analysis."""
    accession_id: str
    species: str
    treatment_vs_control: str
    results: List[DEGResult]
    total_genes: int
    significant_genes: int

class ModelTrainingConfig(BaseModel):
    """Configuration for model training."""
    model_type: str
    hyperparameters: Dict[str, Any]
    random_seed: int
    cv_folds: int

class ModelTrainingResult(BaseModel):
    """Result of model training."""
    model_type: str
    metrics: Dict[str, float]
    feature_importance: Optional[Dict[str, float]] = None

class PathwayMapping(BaseModel):
    """Mapping of genes to pathways."""
    gene_id: str
    pathway_ids: List[str]

class AggregatedFeatures(BaseModel):
    """Aggregated features at the pathway level."""
    accession_id: str
    species: str
    pathway_features: Dict[str, float]

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def create_manifest_entry(file_path: str, accession_id: str, organism: str, source_type: str = "real") -> ManifestEntry:
    """Create a manifest entry for a file."""
    checksum = compute_sha256(file_path)
    return ManifestEntry(
        file_name=os.path.basename(file_path),
        checksum=checksum,
        source_type=source_type,
        accession_id=accession_id,
        organism=organism
    )

def validate_data_manifest(manifest_path: str) -> bool:
    """Validate a data manifest file."""
    try:
        with open(manifest_path, 'r') as f:
            data = json.load(f)
        DataManifest(**data)
        return True
    except Exception as e:
        print(f"Manifest validation failed: {e}")
        return False