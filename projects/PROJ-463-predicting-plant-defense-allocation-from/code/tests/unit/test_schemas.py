"""
Unit tests for data schemas in src/utils/schemas.py
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
from datetime import datetime
from src.utils.schemas import (
    ProvenanceInfo,
    ManifestEntry,
    DataManifest,
    ExpressionMatrixMetadata,
    ExpressionMatrix,
    DefenseTrait,
    TraitDataset,
    DEGResult,
    DEGAnalysisResult,
    ModelTrainingConfig,
    ModelTrainingResult,
    PathwayMapping,
    AggregatedFeatures,
    compute_sha256,
    create_manifest_entry,
    validate_data_manifest
)


class TestProvenanceInfo:
    def test_provenance_creation(self):
        """Test basic ProvenanceInfo creation."""
        provenance = ProvenanceInfo(
            source_type="real",
            source_id="SRA12345",
            tool_versions={"python": "3.11", "numpy": "1.24.0"}
        )
        assert provenance.source_type == "real"
        assert provenance.source_id == "SRA12345"
        assert "python" in provenance.tool_versions
        assert isinstance(provenance.generated_at, datetime)

    def test_provenance_serialization(self):
        """Test ProvenanceInfo serialization."""
        provenance = ProvenanceInfo(
            source_type="synthetic",
            tool_versions={"tool": "1.0"}
        )
        data = provenance.model_dump(mode='json')
        assert 'generated_at' in data
        assert data['source_type'] == 'synthetic'


class TestManifestEntry:
    def test_manifest_entry_creation(self):
        """Test creating a manifest entry."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            temp_path = f.name

        try:
            entry = create_manifest_entry(
                temp_path,
                source_type="synthetic",
                source_id="test-001",
                metadata={"test": True}
            )
            assert entry.file_name == Path(temp_path).name
            assert entry.source_type == "synthetic"
            assert entry.source_id == "test-001"
            assert len(entry.checksum) == 64  # SHA256 hex length
            assert entry.file_size_bytes == 12
        finally:
            os.unlink(temp_path)

    def test_manifest_entry_validation(self):
        """Test that missing file raises error."""
        with pytest.raises(FileNotFoundError):
            create_manifest_entry(
                "/nonexistent/path/file.txt",
                source_type="real"
            )


class TestDataManifest:
    def test_manifest_creation(self):
        """Test creating a DataManifest."""
        manifest = DataManifest()
        assert manifest.manifest_version == "1.0"
        assert len(manifest.entries) == 0

    def test_manifest_add_entry(self):
        """Test adding entries to manifest."""
        manifest = DataManifest()
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            entry = create_manifest_entry(temp_path, "synthetic")
            manifest.add_entry(entry)
            assert len(manifest.entries) == 1
        finally:
            os.unlink(temp_path)

    def test_manifest_serialization(self):
        """Test manifest JSON serialization."""
        manifest = DataManifest()
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            entry = create_manifest_entry(temp_path, "synthetic")
            manifest.add_entry(entry)

            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as json_f:
                json_path = json_f.name

            manifest.to_json(json_path)

            # Load and verify
            with open(json_path, 'r') as f:
                loaded = json.load(f)
            assert len(loaded['entries']) == 1
        finally:
            os.unlink(temp_path)
            os.unlink(json_path)

    def test_manifest_from_json(self):
        """Test loading manifest from JSON."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            entry = create_manifest_entry(temp_path, "synthetic")
            manifest = DataManifest()
            manifest.add_entry(entry)

            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as json_f:
                json_path = json_f.name

            manifest.to_json(json_path)

            loaded = DataManifest.from_json(json_path)
            assert len(loaded.entries) == 1
            assert loaded.entries[0].checksum == entry.checksum
        finally:
            os.unlink(temp_path)
            os.unlink(json_path)


class TestExpressionMatrixMetadata:
    def test_metadata_creation(self):
        """Test ExpressionMatrixMetadata creation."""
        metadata = ExpressionMatrixMetadata(
            matrix_type="tpm",
            organism="Arabidopsis thaliana",
            tissue="leaf",
            gene_count=25000,
            sample_count=10
        )
        assert metadata.matrix_type == "tpm"
        assert metadata.organism == "Arabidopsis thaliana"
        assert metadata.gene_count == 25000


class TestDefenseTrait:
    def test_trait_creation(self):
        """Test DefenseTrait creation."""
        trait = DefenseTrait(
            species_name="Arabidopsis thaliana",
            trait_name="glucosinolate_content",
            trait_value=15.5,
            unit="nmol/mg",
            source_id="TRY-12345",
            source_type="TRY",
            trait_category="chemical"
        )
        assert trait.species_name == "Arabidopsis thaliana"
        assert trait.trait_category == "chemical"
        assert trait.trait_value == 15.5

    def test_trait_validation(self):
        """Test trait validation with invalid category."""
        with pytest.raises(Exception):  # Pydantic validation error
            DefenseTrait(
                species_name="Test",
                trait_name="test",
                trait_value=1.0,
                unit="unit",
                source_id="1",
                source_type="TRY",
                trait_category="invalid_category"
            )


class TestTraitDataset:
    def test_dataset_creation(self):
        """Test TraitDataset creation."""
        trait1 = DefenseTrait(
            species_name="Species A",
            trait_name="trait1",
            trait_value=1.0,
            unit="unit",
            source_id="1",
            source_type="TRY",
            trait_category="chemical"
        )
        trait2 = DefenseTrait(
            species_name="Species B",
            trait_name="trait2",
            trait_value=2.0,
            unit="unit",
            source_id="2",
            source_type="Phenoscape",
            trait_category="physical"
        )

        dataset = TraitDataset(
            dataset_id="test-dataset",
            species_list=["Species A", "Species B"],
            traits=[trait1, trait2],
            source_summary={"TRY": 1, "Phenoscape": 1},
            provenance=ProvenanceInfo(source_type="real")
        )

        assert len(dataset.species_list) == 2
        assert len(dataset.traits) == 2
        assert len(dataset.chemical_traits) == 1
        assert len(dataset.physical_traits) == 1


class TestDEGResult:
    def test_deg_result_creation(self):
        """Test DEGResult creation."""
        result = DEGResult(
            gene_id="AT1G01010",
            gene_name="NAC001",
            log2_fold_change=2.5,
            p_value=0.001,
            adjusted_p_value=0.01,
            base_mean=100.0
        )
        assert result.gene_id == "AT1G01010"
        assert result.log2_fold_change == 2.5
        assert result.significant is True  # adj_p < 0.05 and |log2fc| > 1

    def test_deg_not_significant(self):
        """Test DEGResult with non-significant gene."""
        result = DEGResult(
            gene_id="AT1G01010",
            log2_fold_change=0.5,  # |log2fc| < 1
            p_value=0.001,
            adjusted_p_value=0.01,
            base_mean=100.0
        )
        assert result.significant is False


class TestModelTrainingConfig:
    def test_config_creation(self):
        """Test ModelTrainingConfig creation."""
        config = ModelTrainingConfig(
            model_type="ElasticNet",
            hyperparameters={"alpha": 0.1, "l1_ratio": 0.5},
            cross_validation_type="LOSO",
            random_seed=42,
            target_variable="defense_allocation_index"
        )
        assert config.model_type == "ElasticNet"
        assert config.cv_folds == 5
        assert config.random_seed == 42


class TestPathwayMapping:
    def test_pathway_mapping_creation(self):
        """Test PathwayMapping creation."""
        mapping = PathwayMapping(
            pathway_id="ko00001",
            pathway_name="Test Pathway",
            pathway_source="KEGG",
            gene_ids=["AT1G01010", "AT1G01020"],
            description="A test pathway"
        )
        assert mapping.pathway_id == "ko00001"
        assert len(mapping.gene_ids) == 2
        assert mapping.pathway_source == "KEGG"


class TestComputeSha256:
    def test_sha256_computation(self):
        """Test SHA256 checksum computation."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            temp_path = f.name

        try:
            checksum = compute_sha256(temp_path)
            assert len(checksum) == 64
            assert all(c in '0123456789abcdef' for c in checksum)
        finally:
            os.unlink(temp_path)

    def test_sha256_consistency(self):
        """Test that same file produces same checksum."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            temp_path = f.name

        try:
            checksum1 = compute_sha256(temp_path)
            checksum2 = compute_sha256(temp_path)
            assert checksum1 == checksum2
        finally:
            os.unlink(temp_path)


class TestValidateDataManifest:
    def test_valid_manifest(self):
        """Test validation of a valid manifest."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            entry = create_manifest_entry(temp_path, "synthetic")
            manifest = DataManifest()
            manifest.add_entry(entry)

            errors = validate_data_manifest(manifest)
            assert len(errors) == 0
        finally:
            os.unlink(temp_path)

    def test_manifest_with_missing_file(self):
        """Test validation detects missing file."""
        manifest = DataManifest()
        # Create an entry for a non-existent file
        entry = ManifestEntry(
            file_name="missing.txt",
            file_path="/nonexistent/missing.txt",
            checksum="abc123",
            source_type="synthetic",
            file_size_bytes=100
        )
        manifest.add_entry(entry)

        errors = validate_data_manifest(manifest)
        assert len(errors) > 0
        assert any("not found" in e.lower() for e in errors)

    def test_manifest_with_checksum_mismatch(self):
        """Test validation detects checksum mismatch."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            temp_path = f.name

        try:
            entry = ManifestEntry(
                file_name=Path(temp_path).name,
                file_path=temp_path,
                checksum="wrong_checksum_12345678901234567890123456789012345678901234567890",
                source_type="synthetic",
                file_size_bytes=100
            )
            manifest = DataManifest()
            manifest.add_entry(entry)

            errors = validate_data_manifest(manifest)
            assert len(errors) > 0
            assert any("checksum" in e.lower() for e in errors)
        finally:
            os.unlink(temp_path)