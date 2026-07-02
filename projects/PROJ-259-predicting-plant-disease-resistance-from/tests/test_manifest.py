"""
Tests for the data manifest loader and validator.
"""
import pytest
import yaml
import tempfile
from pathlib import Path
from unittest.mock import patch

from code.data.manifest import (
    load_manifest,
    _validate_manifest_schema,
    get_datasets_by_modality,
    get_dataset_by_accession,
    get_source_type,
    create_default_manifest,
    VALID_SOURCE_TYPES,
    VALID_MODALITIES,
    VALID_STATUSES
)
from code.utils.exceptions import PipelineError, EX_DATA_INTEGRITY


class TestManifestValidation:
    """Test manifest schema validation."""

    def test_valid_manifest(self):
        """Test that a valid manifest passes validation."""
        manifest = {
            "schema_version": "1.0.0",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z",
            "source_type": "SIMULATED",
            "datasets": [
                {
                    "accession_id": "SIM001",
                    "modality": "SNP",
                    "source_url": "internal",
                    "status": "downloaded",
                    "file_path": "data/synthetic_snps.csv"
                }
            ]
        }
        assert _validate_manifest_schema(manifest) is True

    def test_missing_required_field(self):
        """Test validation fails when required field is missing."""
        manifest = {
            "schema_version": "1.0.0",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z",
            "source_type": "SIMULATED",
            "datasets": []
        }
        assert _validate_manifest_schema(manifest) is True  # Empty datasets is allowed but logged

        manifest_no_version = {
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z",
            "source_type": "SIMULATED",
            "datasets": []
        }
        assert _validate_manifest_schema(manifest_no_version) is False

    def test_invalid_source_type(self):
        """Test validation fails with invalid source type."""
        manifest = {
            "schema_version": "1.0.0",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z",
            "source_type": "INVALID",
            "datasets": []
        }
        assert _validate_manifest_schema(manifest) is False

    def test_invalid_modality(self):
        """Test validation fails with invalid modality."""
        manifest = {
            "schema_version": "1.0.0",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z",
            "source_type": "SIMULATED",
            "datasets": [
                {
                    "accession_id": "SIM001",
                    "modality": "INVALID",
                    "source_url": "internal",
                    "status": "downloaded",
                    "file_path": "data/synthetic_snps.csv"
                }
            ]
        }
        assert _validate_manifest_schema(manifest) is False

    def test_invalid_status(self):
        """Test validation fails with invalid status."""
        manifest = {
            "schema_version": "1.0.0",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z",
            "source_type": "SIMULATED",
            "datasets": [
                {
                    "accession_id": "SIM001",
                    "modality": "SNP",
                    "source_url": "internal",
                    "status": "INVALID",
                    "file_path": "data/synthetic_snps.csv"
                }
            ]
        }
        assert _validate_manifest_schema(manifest) is False

    def test_empty_datasets(self):
        """Test validation passes with empty datasets (but logs warning)."""
        manifest = {
            "schema_version": "1.0.0",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z",
            "source_type": "SIMULATED",
            "datasets": []
        }
        assert _validate_manifest_schema(manifest) is True

    def test_missing_dataset_fields(self):
        """Test validation fails when dataset is missing required fields."""
        manifest = {
            "schema_version": "1.0.0",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z",
            "source_type": "SIMULATED",
            "datasets": [
                {
                    "accession_id": "SIM001",
                    "modality": "SNP",
                    "source_url": "internal"
                    # Missing status and file_path
                }
            ]
        }
        assert _validate_manifest_schema(manifest) is False


class TestManifestOperations:
    """Test manifest data operations."""

    def test_get_datasets_by_modality(self):
        """Test filtering datasets by modality."""
        manifest = {
            "schema_version": "1.0.0",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z",
            "source_type": "SIMULATED",
            "datasets": [
                {
                    "accession_id": "SIM001",
                    "modality": "SNP",
                    "source_url": "internal",
                    "status": "downloaded",
                    "file_path": "data/synthetic_snps.csv"
                },
                {
                    "accession_id": "SIM002",
                    "modality": "METABOLITE",
                    "source_url": "internal",
                    "status": "downloaded",
                    "file_path": "data/synthetic_metabolites.csv"
                },
                {
                    "accession_id": "SIM003",
                    "modality": "SNP",
                    "source_url": "internal",
                    "status": "downloaded",
                    "file_path": "data/synthetic_snps2.csv"
                }
            ]
        }
        
        snp_datasets = get_datasets_by_modality(manifest, "SNP")
        assert len(snp_datasets) == 2
        assert all(ds["modality"] == "SNP" for ds in snp_datasets)
        
        metabolite_datasets = get_datasets_by_modality(manifest, "METABOLITE")
        assert len(metabolite_datasets) == 1
        assert metabolite_datasets[0]["accession_id"] == "SIM002"

    def test_get_datasets_by_modality_invalid(self):
        """Test that invalid modality raises ValueError."""
        manifest = {
            "schema_version": "1.0.0",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z",
            "source_type": "SIMULATED",
            "datasets": []
        }
        
        with pytest.raises(ValueError):
            get_datasets_by_modality(manifest, "INVALID")

    def test_get_dataset_by_accession(self):
        """Test finding dataset by accession ID."""
        manifest = {
            "schema_version": "1.0.0",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z",
            "source_type": "SIMULATED",
            "datasets": [
                {
                    "accession_id": "SIM001",
                    "modality": "SNP",
                    "source_url": "internal",
                    "status": "downloaded",
                    "file_path": "data/synthetic_snps.csv"
                }
            ]
        }
        
        dataset = get_dataset_by_accession(manifest, "SIM001")
        assert dataset is not None
        assert dataset["accession_id"] == "SIM001"
        
        missing = get_dataset_by_accession(manifest, "NONEXISTENT")
        assert missing is None

    def test_get_source_type(self):
        """Test getting source type from manifest."""
        manifest = {
            "schema_version": "1.0.0",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z",
            "source_type": "REAL",
            "datasets": []
        }
        
        assert get_source_type(manifest) == "REAL"
        
        manifest["source_type"] = "SIMULATED"
        assert get_source_type(manifest) == "SIMULATED"

    def test_create_default_manifest(self):
        """Test creating a default manifest."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            manifest = create_default_manifest(temp_path)
            
            assert manifest["schema_version"] == "1.0.0"
            assert manifest["source_type"] == "SIMULATED"
            assert manifest["datasets"] == []
            assert "created_at" in manifest
            assert "updated_at" in manifest
            
            # Verify file was written
            assert temp_path.exists()
            with open(temp_path, 'r') as f:
                loaded = yaml.safe_load(f)
            assert loaded == manifest
        finally:
            temp_path.unlink()

class TestLoadManifest:
    """Test loading manifest from file."""

    def test_load_manifest_success(self):
        """Test successful manifest loading."""
        manifest_data = {
            "schema_version": "1.0.0",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z",
            "source_type": "SIMULATED",
            "datasets": []
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(manifest_data, f)
            temp_path = Path(f.name)
        
        try:
            loaded = load_manifest(temp_path)
            assert loaded == manifest_data
        finally:
            temp_path.unlink()

    def test_load_manifest_not_found(self):
        """Test that loading non-existent manifest raises PipelineError."""
        with pytest.raises(PipelineError) as exc_info:
            load_manifest(Path("/nonexistent/path/data_manifest.yaml"))
        
        assert exc_info.value.code == EX_DATA_INTEGRITY.code
        assert "not found" in str(exc_info.value.message).lower()

    def test_load_manifest_invalid_yaml(self):
        """Test that invalid YAML raises PipelineError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(PipelineError) as exc_info:
                load_manifest(temp_path)
            
            assert exc_info.value.code == EX_DATA_INTEGRITY.code
            assert "parse" in str(exc_info.value.message).lower()
        finally:
            temp_path.unlink()

    def test_load_manifest_invalid_schema(self):
        """Test that invalid schema raises PipelineError."""
        manifest_data = {
            "invalid_field": "value"
            # Missing required fields
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(manifest_data, f)
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(PipelineError) as exc_info:
                load_manifest(temp_path)
            
            assert exc_info.value.code == EX_DATA_INTEGRITY.code
            assert "schema validation failed" in str(exc_info.value.message).lower()
        finally:
            temp_path.unlink()