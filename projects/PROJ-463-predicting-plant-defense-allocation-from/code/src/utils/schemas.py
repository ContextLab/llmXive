"""
Data schemas for the plant defense allocation pipeline.
Derived from data-model.md specifications.
"""
from datetime import datetime
from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
import hashlib
import json
import os


class ProvenanceInfo(BaseModel):
    """Provenance metadata for any artifact."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    tool_name: str
    tool_version: str
    input_files: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    checksum: Optional[str] = None
    git_commit: Optional[str] = None


class ManifestEntry(BaseModel):
    """Entry in a data manifest file."""
    file_name: str
    file_path: str
    checksum: str
    source_type: Literal["real", "synthetic", "derived"]
    accession_id: Optional[str] = None
    species: Optional[str] = None
    tissue: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    provenance: Optional[ProvenanceInfo] = None

    @field_validator("checksum")
    @classmethod
    def validate_checksum_format(cls, v: str) -> str:
        if not v or len(v) != 64:
            raise ValueError("Checksum must be a valid SHA256 hex string (64 chars)")
        return v


class DataManifest(BaseModel):
    """Complete manifest for a dataset."""
    manifest_version: str = "1.0"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    description: str
    entries: List[ManifestEntry]
    total_files: int = Field(default=0)

    @model_validator(mode="after")
    def set_total_files(self) -> "DataManifest":
        self.total_files = len(self.entries)
        return self


class ExpressionMatrixMetadata(BaseModel):
    """Metadata for an expression matrix file."""
    accession_id: str
    species: str
    tissue: str
    herbivore_type: Optional[str] = None
    replicates: int
    platform: str
    normalization_method: str = "TPM"
    batch_id: Optional[str] = None
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    housekeeping_genes_cv: Optional[float] = None
    batch_corrected: bool = False


class ExpressionMatrix(BaseModel):
    """
    Expression matrix structure.
    genes: List[str] (row identifiers)
    samples: List[str] (column identifiers)
    values: List[List[float]] (gene x sample matrix)
    metadata: ExpressionMatrixMetadata
    """
    genes: List[str]
    samples: List[str]
    values: List[List[float]]
    metadata: ExpressionMatrixMetadata

    @model_validator(mode="after")
    def validate_dimensions(self) -> "ExpressionMatrix":
        if len(self.values) != len(self.genes):
            raise ValueError("Number of rows in values must match number of genes")
        if any(len(row) != len(self.samples) for row in self.values):
            raise ValueError("All rows in values must have same length as number of samples")
        return self


class DefenseTrait(BaseModel):
    """Individual defense trait record."""
    species_name: str
    trait_name: str
    trait_value: float
    unit: str
    source_id: str  # e.g., TRY ID, Phenoscape ID
    source_type: Literal["TRY", "Phenoscape", "GBIF", "Literature"]
    citation: Optional[str] = None
    notes: Optional[str] = None


class TraitDataset(BaseModel):
    """Collection of defense traits for a species or set of species."""
    species_name: str
    traits: List[DefenseTrait]
    data_sources: List[str]
    compiled_at: datetime = Field(default_factory=datetime.utcnow)


class DEGResult(BaseModel):
    """Differential expression result for a single gene."""
    gene_id: str
    log2_fold_change: float
    p_value: float
    adj_p_value: float  # FDR adjusted
    base_mean: float
    status: Literal["up", "down", "ns"]  # ns = not significant


class DEGAnalysisResult(BaseModel):
    """Results of a differential expression analysis for a species-tissue pair."""
    accession_ids: List[str]
    species: str
    tissue: str
    treatment_condition: str
    control_condition: str
    results: List[DEGResult]
    analysis_params: Dict[str, Any]
    run_at: datetime = Field(default_factory=datetime.utcnow)


class ModelTrainingConfig(BaseModel):
    """Configuration for model training."""
    model_type: Literal["ElasticNet", "RandomForest", "SVM", "XGBoost"]
    hyperparameters: Dict[str, Any]
    cv_folds: int = 5
    random_seed: int = 42
    feature_selection_method: Optional[str] = None
    feature_selection_params: Optional[Dict[str, Any]] = None


class ModelTrainingResult(BaseModel):
    """Results from model training."""
    model_type: str
    config: ModelTrainingConfig
    metrics: Dict[str, float]  # e.g., {"r2": 0.85, "rmse": 0.12}
    feature_importance: Optional[Dict[str, float]] = None
    best_params: Optional[Dict[str, Any]] = None
    trained_at: datetime = Field(default_factory=datetime.utcnow)
    cross_validation_scores: Optional[List[float]] = None


class PathwayMapping(BaseModel):
    """Mapping from genes to pathways."""
    gene_id: str
    pathway_ids: List[str]
    pathway_names: Optional[List[str]] = None
    source: str = "KEGG"  # or "GO"


class AggregatedFeatures(BaseModel):
    """Pathway-aggregated feature matrix."""
    samples: List[str]
    pathways: List[str]
    values: List[List[float]]  # samples x pathways
    aggregation_method: str = "mean"  # or "max", "median"
    metadata: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def validate_dimensions(self) -> "AggregatedFeatures":
        if len(self.values) != len(self.samples):
            raise ValueError("Number of rows in values must match number of samples")
        if any(len(row) != len(self.pathways) for row in self.values):
            raise ValueError("All rows in values must have same length as number of pathways")
        return self


def compute_sha256(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def create_manifest_entry(
    file_path: str,
    source_type: Literal["real", "synthetic", "derived"],
    accession_id: Optional[str] = None,
    species: Optional[str] = None,
    tissue: Optional[str] = None,
    provenance: Optional[ProvenanceInfo] = None
) -> ManifestEntry:
    """Create a manifest entry for a file."""
    checksum = compute_sha256(file_path)
    return ManifestEntry(
        file_name=os.path.basename(file_path),
        file_path=file_path,
        checksum=checksum,
        source_type=source_type,
        accession_id=accession_id,
        species=species,
        tissue=tissue,
        provenance=provenance
    )


def validate_data_manifest(manifest_path: str) -> bool:
    """Validate a data manifest file."""
    try:
        with open(manifest_path, "r") as f:
            data = json.load(f)
        manifest = DataManifest(**data)
        return True
    except Exception as e:
        raise ValueError(f"Invalid manifest: {e}")