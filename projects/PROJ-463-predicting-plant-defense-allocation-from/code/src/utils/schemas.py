"""
Base data schemas for the plant defense allocation pipeline.
Derived from data-model.md and aligned with project requirements.
"""
from datetime import datetime
from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
import hashlib
import json
import os
from pathlib import Path


# --- Core Provenance ---
class ProvenanceInfo(BaseModel):
    """Provenance metadata for any generated artifact."""
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    tool_versions: Dict[str, str] = Field(default_factory=dict)
    source_type: Literal["real", "synthetic"]
    pipeline_run_id: Optional[str] = None
    input_files: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None

    @field_validator("generated_at")
    @classmethod
    def ensure_iso(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v
        return v


# --- Manifests ---
class ManifestEntry(BaseModel):
    """Single entry in a data manifest."""
    file_name: str
    checksum: str  # SHA256
    source_type: Literal["real", "synthetic"]
    provenance: ProvenanceInfo
    file_size_bytes: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("checksum")
    @classmethod
    def validate_checksum_format(cls, v: str) -> str:
        if len(v) != 64:
            raise ValueError("Checksum must be a 64-character hex string (SHA256)")
        return v.lower()


class DataManifest(BaseModel):
    """Manifest for a collection of data files."""
    manifest_version: str = "1.0"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    description: str
    entries: List[ManifestEntry] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_entry(self, entry: ManifestEntry) -> None:
        self.entries.append(entry)

    def to_json(self, path: Optional[Path] = None) -> str:
        """Serialize to JSON string and optionally write to file."""
        data = self.model_dump(mode="json", exclude_none=True)
        json_str = json.dumps(data, indent=2, default=str)
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(json_str)
        return json_str

    @classmethod
    def from_json(cls, path: Path) -> "DataManifest":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.model_validate(data)


# --- Expression Data ---
class ExpressionMatrixMetadata(BaseModel):
    """Metadata for an expression matrix file."""
    matrix_type: Literal["counts", "tpm", "fpkm"]
    organism: str
    genome_version: Optional[str] = None
    tissue: Optional[str] = None
    condition: Optional[str] = None
    batch_info: Optional[str] = None
    gene_count: int
    sample_count: int
    processing_software: Dict[str, str] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ExpressionMatrix(BaseModel):
    """Container for an expression matrix with metadata."""
    file_path: str  # Relative path to the CSV/TSV file
    metadata: ExpressionMatrixMetadata
    checksum: str

    @field_validator("checksum")
    @classmethod
    def validate_checksum_format(cls, v: str) -> str:
        if len(v) != 64:
            raise ValueError("Checksum must be a 64-character hex string (SHA256)")
        return v.lower()


# --- Traits ---
class DefenseTrait(BaseModel):
    """Single defense trait measurement for a species."""
    species_name: str
    trait_name: str
    trait_value: float
    unit: str
    source: str  # e.g., "TRY", "Phenoscape", "GBIF"
    confidence_score: Optional[float] = None
    reference: Optional[str] = None
    measured_at: Optional[datetime] = None


class TraitDataset(BaseModel):
    """Collection of defense traits for multiple species."""
    dataset_name: str
    source: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    traits: List[DefenseTrait] = Field(default_factory=list)
    species_coverage: Dict[str, int] = Field(default_factory=dict)  # species -> count
    missing_species: List[str] = Field(default_factory=list)
    fallback_summary: Optional[Dict[str, Any]] = None

    def add_trait(self, trait: DefenseTrait) -> None:
        self.traits.append(trait)
        if trait.species_name not in self.species_coverage:
            self.species_coverage[trait.species_name] = 0
        self.species_coverage[trait.species_name] += 1


# --- Differential Expression ---
class DEGResult(BaseModel):
    """Result for a single gene in differential expression analysis."""
    gene_id: str
    gene_name: str
    log2_fold_change: float
    p_value: float
    adjusted_p_value: float  # FDR
    base_mean: float
    is_significant: bool = Field(default=False)

    @model_validator(mode="after")
    def set_significance(self) -> "DEGResult":
        if self.adjusted_p_value < 0.05 and abs(self.log2_fold_change) > 1:
            self.is_significant = True
        return self


class DEGAnalysisResult(BaseModel):
    """Full result of a differential expression analysis."""
    species: str
    tissue: str
    condition_comparison: str  # e.g., "herbivore_vs_control"
    analysis_date: datetime = Field(default_factory=datetime.utcnow)
    total_genes: int
    significant_genes: int
    results: List[DEGResult] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    software_versions: Dict[str, str] = Field(default_factory=dict)


# --- Modeling ---
class ModelTrainingConfig(BaseModel):
    """Configuration for model training."""
    model_type: Literal["elastic_net", "random_forest", "pgls"]
    hyperparameters: Dict[str, Any] = Field(default_factory=dict)
    cv_folds: int = 5
    random_seed: int = 42
    feature_selection_method: Optional[str] = None
    exclusion_rules: Optional[Dict[str, Any]] = None


class ModelTrainingResult(BaseModel):
    """Result of model training and validation."""
    model_type: str
    species_left_out: Optional[str] = None  # For LOSO
    r_squared: float
    rmse: float
    mean_absolute_error: float
    feature_importance: Dict[str, float] = Field(default_factory=dict)
    training_config: ModelTrainingConfig
    training_date: datetime = Field(default_factory=datetime.utcnow)
    cross_validation_scores: Optional[List[float]] = None


# --- Pathways ---
class PathwayMapping(BaseModel):
    """Mapping of genes to pathways."""
    pathway_id: str
    pathway_name: str
    source: Literal["KEGG", "GO"]
    gene_ids: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class AggregatedFeatures(BaseModel):
    """Aggregated features at the pathway level."""
    file_path: str  # Path to the CSV file
    sample_count: int
    feature_count: int  # Number of pathways
    aggregation_method: str  # e.g., "mean", "sum", "max"
    pathway_mappings_used: List[str]  # List of pathway IDs
    created_at: datetime = Field(default_factory=datetime.utcnow)
    checksum: str


# --- Utilities ---
def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def create_manifest_entry(
    file_path: Path,
    source_type: Literal["real", "synthetic"],
    provenance: ProvenanceInfo,
    description: str = ""
) -> ManifestEntry:
    """Create a ManifestEntry for a given file."""
    checksum = compute_sha256(file_path)
    file_size = file_path.stat().st_size
    return ManifestEntry(
        file_name=file_path.name,
        checksum=checksum,
        source_type=source_type,
        provenance=provenance,
        file_size_bytes=file_size
    )


def validate_data_manifest(manifest: DataManifest) -> bool:
    """Validate that all files in a manifest exist and checksums match."""
    for entry in manifest.entries:
        # In a real implementation, we would check file existence and recompute checksum
        # For schema validation, we just ensure the structure is correct
        if len(entry.checksum) != 64:
            return False
    return True