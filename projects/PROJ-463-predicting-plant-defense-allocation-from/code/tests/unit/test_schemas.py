"""
Unit tests for data schemas defined in src/utils/schemas.py.
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
    ModelTrainingConfig,
    PathwayMapping,
    AggregatedFeatures,
    compute_sha256,
    create_manifest_entry,
    validate_data_manifest
)


class TestProvenanceInfo:
    def test_valid_provenance(self):
        p = ProvenanceInfo(
            generated_at=datetime.utcnow(),
            tool_versions={"python": "3.11"},
            source_type="real",
            raw_source_id="SRA12345"
        )
        assert p.source_type == "real"
        assert "python" in p.tool_versions

    def test_invalid_source_type(self):
        with pytest.raises(ValueError):
            ProvenanceInfo(
                generated_at=datetime.utcnow(),
                tool_versions={},
                source_type="invalid_type"
            )


class TestManifestEntry:
    def test_valid_entry(self):
        p_info = ProvenanceInfo(
            generated_at=datetime.utcnow(),
            tool_versions={},
            source_type="synthetic"
        )
        entry = ManifestEntry(
            file_name="test.csv",
            file_path="data/synthetic/test.csv",
            checksum="abc123",
            source_type="synthetic",
            provenance=p_info
        )
        assert entry.file_name == "test.csv"
        assert entry.checksum == "abc123"


class TestDataManifest:
    def test_add_entry(self):
        manifest = DataManifest()
        p_info = ProvenanceInfo(
            generated_at=datetime.utcnow(),
            tool_versions={},
            source_type="synthetic"
        )
        entry = ManifestEntry(
            file_name="test.csv",
            file_path="data/synthetic/test.csv",
            checksum="abc123",
            source_type="synthetic",
            provenance=p_info
        )
        manifest.add_entry(entry)
        assert len(manifest.entries) == 1

    def test_get_entry_by_name(self):
        manifest = DataManifest()
        p_info = ProvenanceInfo(
            generated_at=datetime.utcnow(),
            tool_versions={},
            source_type="synthetic"
        )
        entry = ManifestEntry(
            file_name="test.csv",
            file_path="data/synthetic/test.csv",
            checksum="abc123",
            source_type="synthetic",
            provenance=p_info
        )
        manifest.add_entry(entry)
        found = manifest.get_entry_by_name("test.csv")
        assert found is not None
        assert found.file_name == "test.csv"
        not_found = manifest.get_entry_by_name("missing.csv")
        assert not_found is None


class TestExpressionMatrixMetadata:
    def test_valid_metadata(self):
        meta = ExpressionMatrixMetadata(
            matrix_type="TPM",
            species="Arabidopsis thaliana",
            tissue="leaf",
            accession_id="SRA123",
            gene_count=20000,
            sample_count=10,
            processing_pipeline_version="1.0"
        )
        assert meta.species == "Arabidopsis thaliana"
        assert meta.matrix_type == "TPM"


class TestDefenseTrait:
    def test_valid_trait(self):
        trait = DefenseTrait(
            species_name="Zea mays",
            trait_name="Cyanogenic_potential",
            trait_value=5.5,
            source_id="TRY_123",
            source_database="TRY"
        )
        assert trait.trait_value == 5.5
        assert trait.source_database == "TRY"


class TestTraitDataset:
    def test_valid_dataset(self):
        trait = DefenseTrait(
            species_name="Zea mays",
            trait_name="Cyanogenic_potential",
            trait_value=5.5,
            source_id="TRY_123",
            source_database="TRY"
        )
        dataset = TraitDataset(
            species_list=["Zea mays"],
            traits=[trait]
        )
        assert len(dataset.species_list) == 1
        assert len(dataset.traits) == 1


class TestDEGResult:
    def test_valid_deg(self):
        deg = DEGResult(
            gene_id="AT1G01010",
            log2_fold_change=2.5,
            p_value=0.001,
            padj=0.01,
            base_mean=100.0,
            species_tissue="Arabidopsis_thaliana_leaf",
            comparison="herbivore_vs_control"
        )
        assert deg.log2_fold_change == 2.5
        assert deg.padj < 0.05


class TestModelTrainingConfig:
    def test_valid_config(self):
        config = ModelTrainingConfig(
            model_type="ElasticNet",
            hyperparameters={"alpha": 0.1},
            cv_folds=5
        )
        assert config.model_type == "ElasticNet"
        assert config.hyperparameters["alpha"] == 0.1


class TestPathwayMapping:
    def test_valid_mapping(self):
        mapping = PathwayMapping(
            gene_id="AT1G01010",
            pathway_ids=["map00010"],
            database="KEGG"
        )
        assert "map00010" in mapping.pathway_ids


class TestAggregatedFeatures:
    def test_valid_features(self):
        feats = AggregatedFeatures(
            sample_id="sample_01",
            species="Zea mays",
            pathway_scores={"map00010": 0.5, "map00020": 0.8},
            aggregation_method="mean"
        )
        assert len(feats.pathway_scores) == 2


class TestComputeSha256:
    def test_compute_checksum(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            checksum = compute_sha256(temp_path)
            assert len(checksum) == 64  # SHA256 hex length
        finally:
            os.unlink(temp_path)

    def test_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            compute_sha256("/nonexistent/path/file.txt")


class TestValidateDataManifest:
    def test_valid_manifest(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            data = {
                "manifest_version": "1.0",
                "created_at": datetime.utcnow().isoformat(),
                "entries": []
            }
            json.dump(data, f)
            temp_path = f.name

        try:
            assert validate_data_manifest(temp_path) is True
        finally:
            os.unlink(temp_path)

    def test_invalid_manifest(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json")
            temp_path = f.name

        try:
            assert validate_data_manifest(temp_path) is False
        finally:
            os.unlink(temp_path)