"""
Base data schemas derived from data-model.md.

Defines Pydantic models for validation of data structures used throughout the
plant defense allocation pipeline, including raw data manifests, processed
expression matrices, and trait data.
"""

from datetime import datetime
from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
import hashlib
import json


# --- Manifest Schemas ---

class ProvenanceInfo(BaseModel):
    """Provenance metadata for a data file."""
    generated_at: datetime = Field(..., description="ISO8601 timestamp of generation")
    tool_versions: Dict[str, str] = Field(
        ..., 
        description="Version strings for tools used (e.g., python, numpy)"
    )
    source_type: Literal["real", "synthetic"] = Field(
        ..., 
        description="Whether data is from real source or synthetic generation"
    )
    checksum: Optional[str] = Field(None, description="SHA256 checksum of the file")
    notes: Optional[str] = Field(None, description="Additional provenance notes")

class ManifestEntry(BaseModel):
    """A single entry in a data manifest."""
    file_name: str = Field(..., description="Relative path to the file")
    checksum: str = Field(..., description="SHA256 checksum of the file")
    source_type: Literal["real", "synthetic"] = Field(
        ..., 
        description="Origin of the data"
    )
    provenance: ProvenanceInfo = Field(..., description="Detailed provenance info")
    file_size_bytes: Optional[int] = Field(None, description="Size of the file in bytes")

class DataManifest(BaseModel):
    """A complete manifest for a dataset or collection."""
    manifest_version: str = Field("1.0", description="Version of the manifest schema")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    entries: List[ManifestEntry] = Field(..., description="List of file entries")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @model_validator(mode='before')
    @classmethod
    def validate_entries(cls, values: dict) -> dict:
        """Ensure all entries have valid source types and checksums."""
        if 'entries' in values:
            for entry in values['entries']:
                if isinstance(entry, dict):
                    if entry.get('source_type') not in ['real', 'synthetic']:
                        raise ValueError("source_type must be 'real' or 'synthetic'")
                    if not entry.get('checksum'):
                        raise ValueError("checksum is required for all entries")
        return values

# --- Expression Data Schemas ---

class ExpressionMatrixMetadata(BaseModel):
    """Metadata for an expression matrix."""
    matrix_type: Literal["TPM", "FPKM", "Counts", "Normalized"] = Field(
        ..., 
        description="Type of expression values"
    )
    species: str = Field(..., description="Target species name")
    tissue: str = Field(..., description="Tissue type")
    experiment_id: str = Field(..., description="Unique experiment identifier")
    n_genes: int = Field(..., description="Number of genes in the matrix")
    n_samples: int = Field(..., description="Number of samples in the matrix")
    normalization_method: Optional[str] = Field(None, description="Method used for normalization")
    batch_corrected: bool = Field(False, description="Whether batch correction was applied")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")

class ExpressionMatrix(BaseModel):
    """
    Container for an expression matrix and its metadata.
    
    Note: The actual data (genes x samples) is stored separately in CSV/Parquet
    files; this schema validates the associated metadata and structure.
    """
    metadata: ExpressionMatrixMetadata = Field(..., description="Matrix metadata")
    gene_ids: List[str] = Field(..., description="List of gene identifiers (rows)")
    sample_ids: List[str] = Field(..., description="List of sample identifiers (columns)")
    data_path: str = Field(..., description="Path to the actual data file")

    @field_validator('gene_ids')
    @classmethod
    def validate_gene_ids(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("gene_ids cannot be empty")
        return v

    @field_validator('sample_ids')
    @classmethod
    def validate_sample_ids(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("sample_ids cannot be empty")
        return v

# --- Trait Data Schemas ---

class DefenseTrait(BaseModel):
    """A single defense trait measurement."""
    species: str = Field(..., description="Species name")
    trait_type: Literal["chemical", "physical", "behavioral"] = Field(
        ..., 
        description="Category of the trait"
    )
    trait_name: str = Field(..., description="Specific trait name")
    value: float = Field(..., description="Measured value")
    unit: str = Field(..., description="Unit of measurement")
    source: str = Field(..., description="Source database or publication")
    confidence_score: Optional[float] = Field(None, description="Confidence in the measurement")
    reference_id: Optional[str] = Field(None, description="Reference identifier")

class TraitDataset(BaseModel):
    """A collection of defense traits."""
    dataset_id: str = Field(..., description="Unique dataset identifier")
    source: str = Field(..., description="Primary source (e.g., TRY, Phenoscape)")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    n_species: int = Field(..., description="Number of unique species")
    n_traits: int = Field(..., description="Number of trait records")
    traits: List[DefenseTrait] = Field(..., description="List of trait records")
    fallback_used: bool = Field(False, description="Whether fallback sources were used")

    @model_validator(mode='after')
    def count_species_and_traits(self) -> 'TraitDataset':
        """Update counts based on actual data."""
        unique_species = set(t.species for t in self.traits)
        self.n_species = len(unique_species)
        self.n_traits = len(self.traits)
        return self

# --- Differential Expression Schemas ---

class DEGResult(BaseModel):
    """Differential expression result for a single gene."""
    gene_id: str = Field(..., description="Gene identifier")
    log2_fold_change: float = Field(..., description="Log2 fold change")
    p_value: float = Field(..., description="Raw p-value")
    adj_p_value: float = Field(..., description="Adjusted p-value (FDR)")
    base_mean: float = Field(..., description="Mean normalized count")
    significant: bool = Field(..., description="Whether gene is significant (FDR < 0.05, |log2FC| > 1)")

class DEGAnalysisResult(BaseModel):
    """Results from a differential expression analysis."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    species: str = Field(..., description="Species name")
    tissue: str = Field(..., description="Tissue type")
    condition_a: str = Field(..., description="Control condition")
    condition_b: str = Field(..., description="Treatment condition")
    n_genes_tested: int = Field(..., description="Number of genes tested")
    n_significant: int = Field(..., description="Number of significant genes")
    results: List[DEGResult] = Field(..., description="Per-gene results")
    method: str = Field("DESeq2", description="Method used for analysis")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")

# --- Model Training Schemas ---

class ModelTrainingConfig(BaseModel):
    """Configuration for model training."""
    model_type: str = Field(..., description="Type of model (e.g., ElasticNet, RandomForest)")
    hyperparameters: Dict[str, Any] = Field(default_factory=dict, description="Model hyperparameters")
    cv_folds: int = Field(5, description="Number of cross-validation folds")
    random_seed: int = Field(42, description="Random seed for reproducibility")
    feature_selection_method: Optional[str] = Field(None, description="Feature selection method used")

class ModelTrainingResult(BaseModel):
    """Results from model training."""
    model_id: str = Field(..., description="Unique model identifier")
    config: ModelTrainingConfig = Field(..., description="Training configuration")
    metrics: Dict[str, float] = Field(..., description="Performance metrics (R2, RMSE, etc.)")
    feature_importance: Optional[Dict[str, float]] = Field(None, description="Feature importance scores")
    training_samples: int = Field(..., description="Number of training samples")
    test_samples: int = Field(..., description="Number of test samples")
    training_time_seconds: float = Field(..., description="Time taken for training")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")

# --- Pathway Aggregation Schemas ---

class PathwayMapping(BaseModel):
    """Mapping of genes to pathways."""
    pathway_id: str = Field(..., description="Pathway identifier (KEGG/GO)")
    pathway_name: str = Field(..., description="Pathway name")
    gene_ids: List[str] = Field(..., description="List of gene IDs in this pathway")
    source: str = Field(..., description="Source of the mapping (KEGG, GO, etc.)")

class AggregatedFeatures(BaseModel):
    """Aggregated feature matrix based on pathways."""
    matrix_id: str = Field(..., description="Unique matrix identifier")
    n_samples: int = Field(..., description="Number of samples")
    n_features: int = Field(..., description="Number of pathway features (must be <= 50)")
    pathway_ids: List[str] = Field(..., description="List of pathway identifiers")
    sample_ids: List[str] = Field(..., description="List of sample identifiers")
    data_path: str = Field(..., description="Path to the aggregated data file")
    aggregation_method: str = Field("mean", description="Method used for aggregation")

    @field_validator('n_features')
    @classmethod
    def validate_feature_count(cls, v: int) -> int:
        if v > 50:
            raise ValueError("Number of aggregated features must be <= 50")
        return v

# --- Utility Functions ---

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def create_manifest_entry(
    file_path: str,
    source_type: Literal["real", "synthetic"],
    tool_versions: Dict[str, str],
    notes: Optional[str] = None
) -> ManifestEntry:
    """Create a manifest entry for a file."""
    checksum = compute_sha256(file_path)
    file_size = Path(file_path).stat().st_size
    
    return ManifestEntry(
        file_name=str(file_path),
        checksum=checksum,
        source_type=source_type,
        provenance=ProvenanceInfo(
            generated_at=datetime.utcnow(),
            tool_versions=tool_versions,
            source_type=source_type,
            checksum=checksum,
            notes=notes
        ),
        file_size_bytes=file_size
    )

def validate_data_manifest(manifest: DataManifest) -> bool:
    """Validate a data manifest."""
    try:
        manifest.model_validate(manifest.model_dump())
        return True
    except Exception:
        return False
    

# Export public API
__all__ = [
    "ProvenanceInfo",
    "ManifestEntry",
    "DataManifest",
    "ExpressionMatrixMetadata",
    "ExpressionMatrix",
    "DefenseTrait",
    "TraitDataset",
    "DEGResult",
    "DEGAnalysisResult",
    "ModelTrainingConfig",
    "ModelTrainingResult",
    "PathwayMapping",
    "AggregatedFeatures",
    "compute_sha256",
    "create_manifest_entry",
    "validate_data_manifest"
]