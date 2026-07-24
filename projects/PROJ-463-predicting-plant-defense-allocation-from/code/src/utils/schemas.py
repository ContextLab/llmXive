"""
Data schemas for the plant defense allocation pipeline.
Derived from data-model.md and aligned with project requirements.
"""
from datetime import datetime
from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
import hashlib
import json
import os
from pathlib import Path


class ProvenanceInfo(BaseModel):
    """Provenance metadata for data artifacts."""
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    tool_versions: Dict[str, str] = Field(default_factory=dict)
    source_type: Literal["real", "synthetic"]
    source_id: Optional[str] = None  # e.g., SRA accession, DOI
    pipeline_version: Optional[str] = None
    config_hash: Optional[str] = None


class ManifestEntry(BaseModel):
    """Entry in a data manifest file."""
    file_name: str
    file_path: str  # Relative to project root
    checksum: str  # SHA256
    source_type: Literal["real", "synthetic"]
    source_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    file_size_bytes: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DataManifest(BaseModel):
    """Manifest for a collection of data files."""
    manifest_version: str = "1.0"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    entries: List[ManifestEntry] = []
    summary: Dict[str, Any] = Field(default_factory=dict)

    def add_entry(self, entry: ManifestEntry) -> None:
        """Add an entry to the manifest."""
        self.entries.append(entry)
        self.updated_at = datetime.utcnow()

    def to_json(self, path: str) -> None:
        """Serialize manifest to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.model_dump(mode='json', exclude_none=True), f, indent=2)

    @classmethod
    def from_json(cls, path: str) -> "DataManifest":
        """Load manifest from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(**data)


class ExpressionMatrixMetadata(BaseModel):
    """Metadata for an expression matrix."""
    matrix_type: Literal["counts", "tpm", "fpkm", "normalized"]
    organism: str
    tissue: Optional[str] = None
    condition: Optional[str] = None
    study_id: Optional[str] = None
    gene_count: int
    sample_count: int
    normalization_method: Optional[str] = None
    batch_info: Optional[Dict[str, Any]] = None


class ExpressionMatrix(BaseModel):
    """Container for expression matrix data and metadata."""
    matrix_id: str
    metadata: ExpressionMatrixMetadata
    data_path: str  # Path to the actual matrix file (e.g., CSV, Parquet)
    provenance: ProvenanceInfo

    @field_validator('data_path')
    @classmethod
    def validate_path_exists(cls, v: str) -> str:
        if not os.path.exists(v):
            raise ValueError(f"Data file does not exist: {v}")
        return v


class DefenseTrait(BaseModel):
    """Individual defense trait measurement."""
    species_name: str
    trait_name: str
    trait_value: float
    unit: str
    source_id: str  # e.g., TRY accession, Phenoscape ID
    source_type: Literal["TRY", "Phenoscape", "GBIF", "Literature"]
    trait_category: Literal["chemical", "physical", "behavioral"]
    measured_at: Optional[datetime] = None
    notes: Optional[str] = None


class TraitDataset(BaseModel):
    """Collection of defense traits for multiple species."""
    dataset_id: str
    species_list: List[str]
    traits: List[DefenseTrait]
    source_summary: Dict[str, int]  # source_type -> count
    created_at: datetime = Field(default_factory=datetime.utcnow)
    provenance: ProvenanceInfo

    @property
    def chemical_traits(self) -> List[DefenseTrait]:
        return [t for t in self.traits if t.trait_category == "chemical"]

    @property
    def physical_traits(self) -> List[DefenseTrait]:
        return [t for t in self.traits if t.trait_category == "physical"]


class DEGResult(BaseModel):
    """Differential expression result for a single gene."""
    gene_id: str
    gene_name: Optional[str] = None
    log2_fold_change: float
    p_value: float
    adjusted_p_value: float
    base_mean: float
    significant: bool = False

    @field_validator('significant')
    @classmethod
    def compute_significance(cls, v: bool, info) -> bool:
        # Default threshold: adjusted p-value < 0.05 and |log2FC| > 1
        if 'adjusted_p_value' in info.data and 'log2_fold_change' in info.data:
            adj_p = info.data['adjusted_p_value']
            log2fc = info.data['log2_fold_change']
            return adj_p < 0.05 and abs(log2fc) > 1
        return v


class DEGAnalysisResult(BaseModel):
    """Result of a differential expression analysis."""
    analysis_id: str
    species: str
    tissue: Optional[str] = None
    condition_comparison: str  # e.g., "herbivore_vs_control"
    results: List[DEGResult]
    total_genes_tested: int
    significant_genes_count: int
    analysis_method: str = "DESeq2"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    provenance: ProvenanceInfo


class ModelTrainingConfig(BaseModel):
    """Configuration for model training."""
    model_type: Literal["ElasticNet", "RandomForest", "SVR", "PGLS"]
    hyperparameters: Dict[str, Any]
    feature_selection_method: Optional[str] = None
    cross_validation_type: Literal["LOSO", "KFold", "StratifiedKFold"]
    cv_folds: int = 5
    random_seed: int = 42
    target_variable: str = "defense_allocation_index"


class ModelTrainingResult(BaseModel):
    """Result of model training and validation."""
    training_id: str
    config: ModelTrainingConfig
    metrics: Dict[str, float]  # e.g., {"r2": 0.75, "rmse": 0.12}
    feature_importance: Optional[Dict[str, float]] = None
    best_params: Optional[Dict[str, Any]] = None
    cv_results: Optional[List[Dict[str, float]]] = None  # Per-fold metrics
    training_data_path: Optional[str] = None
    test_data_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    provenance: ProvenanceInfo


class PathwayMapping(BaseModel):
    """Mapping from genes to pathways."""
    pathway_id: str
    pathway_name: str
    pathway_source: Literal["KEGG", "GO", "Reactome"]
    gene_ids: List[str]
    description: Optional[str] = None


class AggregatedFeatures(BaseModel):
    """Pathway-aggregated feature matrix."""
    matrix_id: str
    species_list: List[str]
    pathway_ids: List[str]
    feature_matrix_path: str  # Path to the aggregated matrix file
    aggregation_method: str  # e.g., "mean", "max", "first_pcs"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    provenance: ProvenanceInfo


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
    source_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> ManifestEntry:
    """Create a manifest entry for a file."""
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    checksum = compute_sha256(file_path)
    file_size = file_path_obj.stat().st_size

    return ManifestEntry(
        file_name=file_path_obj.name,
        file_path=str(file_path_obj),
        checksum=checksum,
        source_type=source_type,
        source_id=source_id,
        file_size_bytes=file_size,
        metadata=metadata or {}
    )


def validate_data_manifest(manifest: DataManifest) -> List[str]:
    """Validate a data manifest. Returns list of error messages."""
    errors = []

    # Check for duplicate file names
    seen_names = set()
    for entry in manifest.entries:
        if entry.file_name in seen_names:
            errors.append(f"Duplicate file name in manifest: {entry.file_name}")
        seen_names.add(entry.file_name)

    # Verify all files exist and checksums match
    for entry in manifest.entries:
        if not os.path.exists(entry.file_path):
            errors.append(f"File not found: {entry.file_path}")
        else:
            actual_checksum = compute_sha256(entry.file_path)
            if actual_checksum != entry.checksum:
                errors.append(
                    f"Checksum mismatch for {entry.file_path}: "
                    f"expected {entry.checksum}, got {actual_checksum}"
                )

    return errors
