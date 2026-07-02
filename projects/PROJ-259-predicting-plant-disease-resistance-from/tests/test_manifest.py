"""
Tests for the data manifest loader and utilities.
"""
import os
import tempfile
import pytest
import yaml
from pathlib import Path

from code.data.manifest import (
    load_manifest,
    save_manifest,
    get_dataset_by_id,
    add_dataset,
    update_dataset_status,
    get_datasets_by_modality,
    get_source_type,
    is_simulation_mode,
    MANIFEST_SCHEMA,
)

@pytest.fixture
def temp_manifest_path():
    """Create a temporary manifest file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        manifest_data = {
            "version": "1.0",
            "source_type": "SIMULATED",
            "datasets": [
                {
                    "dataset_id": "test_snp_001",
                    "source": "synthetic",
                    "modality": "SNP",
                    "file_path": "data/raw/test_snps.csv",
                    "status": "pending",
                    "accession": None,
                    "checksum": None,
                    "metadata": {}
                },
                {
                    "dataset_id": "test_metab_001",
                    "source": "synthetic",
                    "modality": "metabolite",
                    "file_path": "data/raw/test_metabolites.csv",
                    "status": "pending",
                    "accession": None,
                    "checksum": None,
                    "metadata": {}
                }
            ]
        }
        yaml.dump(manifest_data, f)
        temp_path = Path(f.name)
    yield temp_path
    os.unlink(temp_path)

def test_load_manifest_exists(temp_manifest_path):
    """Test loading an existing manifest file."""
    manifest = load_manifest(temp_manifest_path)
    
    assert manifest["version"] == "1.0"
    assert manifest["source_type"] == "SIMULATED"
    assert len(manifest["datasets"]) == 2
    
    # Check dataset structure
    snp_dataset = get_dataset_by_id(manifest, "test_snp_001")
    assert snp_dataset is not None
    assert snp_dataset["modality"] == "SNP"
    
    metab_dataset = get_dataset_by_id(manifest, "test_metab_001")
    assert metab_dataset is not None
    assert metab_dataset["modality"] == "metabolite"

def test_load_manifest_missing_file():
    """Test loading a non-existent manifest file creates default."""
    with tempfile.TemporaryDirectory() as tmpdir:
        missing_path = Path(tmpdir) / "missing_manifest.yaml"
        manifest = load_manifest(missing_path)
        
        assert os.path.exists(missing_path)
        assert manifest["source_type"] == "SIMULATED"
        assert manifest["version"] == "1.0"
        assert manifest["datasets"] == []

def test_save_and_reload(temp_manifest_path):
    """Test saving and reloading a manifest."""
    # Modify the manifest
    manifest = load_manifest(temp_manifest_path)
    manifest["source_type"] = "REAL"
    
    # Save to a new location
    with tempfile.TemporaryDirectory() as tmpdir:
        new_path = Path(tmpdir) / "new_manifest.yaml"
        save_manifest(manifest, new_path)
        
        # Reload and verify
        reloaded = load_manifest(new_path)
        assert reloaded["source_type"] == "REAL"
        assert len(reloaded["datasets"]) == 2

def test_add_dataset(temp_manifest_path):
    """Test adding a new dataset to the manifest."""
    manifest = load_manifest(temp_manifest_path)
    
    new_dataset = {
        "dataset_id": "test_pheno_001",
        "source": "synthetic",
        "modality": "phenotype",
        "file_path": "data/raw/test_phenotypes.csv",
        "status": "pending"
    }
    
    updated_manifest = add_dataset(manifest, new_dataset)
    
    assert len(updated_manifest["datasets"]) == 3
    added = get_dataset_by_id(updated_manifest, "test_pheno_001")
    assert added is not None
    assert added["modality"] == "phenotype"
    assert added["accession"] is None  # Should be added as None

def test_add_duplicate_dataset(temp_manifest_path):
    """Test that adding a duplicate dataset_id raises an error."""
    manifest = load_manifest(temp_manifest_path)
    
    duplicate_dataset = {
        "dataset_id": "test_snp_001",  # Already exists
        "source": "synthetic",
        "modality": "SNP",
        "file_path": "data/raw/duplicate.csv",
        "status": "pending"
    }
    
    with pytest.raises(ValueError, match="already exists"):
        add_dataset(manifest, duplicate_dataset)

def test_update_dataset_status(temp_manifest_path):
    """Test updating dataset status."""
    manifest = load_manifest(temp_manifest_path)
    
    updated = update_dataset_status(manifest, "test_snp_001", "downloaded")
    dataset = get_dataset_by_id(updated, "test_snp_001")
    assert dataset["status"] == "downloaded"

def test_update_invalid_status(temp_manifest_path):
    """Test updating with an invalid status raises an error."""
    manifest = load_manifest(temp_manifest_path)
    
    with pytest.raises(ValueError, match="Invalid status"):
        update_dataset_status(manifest, "test_snp_001", "invalid_status")

def test_get_datasets_by_modality(temp_manifest_path):
    """Test filtering datasets by modality."""
    manifest = load_manifest(temp_manifest_path)
    
    snp_datasets = get_datasets_by_modality(manifest, "SNP")
    assert len(snp_datasets) == 1
    assert snp_datasets[0]["dataset_id"] == "test_snp_001"
    
    metab_datasets = get_datasets_by_modality(manifest, "metabolite")
    assert len(metab_datasets) == 1
    
    non_existent = get_datasets_by_modality(manifest, "protein")
    assert len(non_existent) == 0

def test_source_type_helpers(temp_manifest_path):
    """Test source type helper functions."""
    manifest = load_manifest(temp_manifest_path)
    
    assert get_source_type(manifest) == "SIMULATED"
    assert is_simulation_mode(manifest) is True
    
    manifest["source_type"] = "REAL"
    assert get_source_type(manifest) == "REAL"
    assert is_simulation_mode(manifest) is False

def test_manifest_schema_validation():
    """Test that manifest schema validation works correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create invalid manifest (missing required fields)
        invalid_manifest = {
            "version": "1.0",
            "source_type": "SIMULATED",
            "datasets": [
                {
                    "dataset_id": "test_001",
                    # Missing required fields: source, modality, file_path, status
                }
            ]
        }
        
        invalid_path = Path(tmpdir) / "invalid.yaml"
        with open(invalid_path, 'w') as f:
            yaml.dump(invalid_manifest, f)
        
        with pytest.raises(ValueError, match="missing required field"):
            load_manifest(invalid_path)