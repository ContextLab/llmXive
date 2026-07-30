import pytest
import pandas as pd
import numpy as np
import json
import tempfile
from pathlib import Path
import sys
import os

# Add the code directory to the path so we can import src modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data.qc import check_replicates, check_metadata_completeness, run_qc_pipeline

class TestQC:
    @pytest.fixture
    def temp_manifest(self):
        """Create a temporary manifest file for testing"""
        manifest_data = {
            "studies": [
                {
                    "accession_id": "SRP000001",
                    "species": "Arabidopsis thaliana",
                    "tissue": "leaf",
                    "treatment": "herbivory",
                    "replicates": 3
                },
                {
                    "accession_id": "SRP000002",
                    "species": "Zea mays",
                    "tissue": "root",
                    "treatment": "drought",
                    "replicates": 1
                },
                {
                    "accession_id": "SRP000003",
                    "species": "Solanum lycopersicum",
                    "tissue": "",
                    "treatment": "pathogen",
                    "replicates": 2
                },
                {
                    "accession_id": "SRP000004",
                    "species": "Oryza sativa",
                    "tissue": "leaf",
                    "treatment": "heat",
                    "replicates": 4
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(manifest_data, f)
            temp_path = Path(f.name)
        
        yield temp_path
        
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for output"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_check_replicates_valid(self):
        """Test check_replicates with valid replicate count"""
        metadata = {"replicates": 3}
        is_valid, reason = check_replicates(metadata, min_replicates=2)
        assert is_valid is True
        assert reason == ""

    def test_check_replicates_insufficient(self):
        """Test check_replicates with insufficient replicates"""
        metadata = {"replicates": 1}
        is_valid, reason = check_replicates(metadata, min_replicates=2)
        assert is_valid is False
        assert "Insufficient biological replicates" in reason

    def test_check_replicates_missing(self):
        """Test check_replicates with missing replicates count"""
        metadata = {}
        is_valid, reason = check_replicates(metadata, min_replicates=2)
        assert is_valid is False
        assert "Missing replicates count" in reason

    def test_check_metadata_completeness_valid(self):
        """Test check_metadata_completeness with valid metadata"""
        metadata = {"tissue": "leaf", "species": "Arabidopsis"}
        is_valid, reason = check_metadata_completeness(metadata, required_fields=['tissue', 'species'])
        assert is_valid is True
        assert reason == ""

    def test_check_metadata_completeness_missing_field(self):
        """Test check_metadata_completeness with missing field"""
        metadata = {"tissue": "leaf"}
        is_valid, reason = check_metadata_completeness(metadata, required_fields=['tissue', 'species'])
        assert is_valid is False
        assert "Missing required metadata fields" in reason
        assert "species" in reason

    def test_check_metadata_completeness_empty_field(self):
        """Test check_metadata_completeness with empty field value"""
        metadata = {"tissue": "", "species": "Arabidopsis"}
        is_valid, reason = check_metadata_completeness(metadata, required_fields=['tissue'])
        assert is_valid is False
        assert "Missing required metadata fields" in reason
        assert "tissue" in reason

    def test_run_qc_pipeline(self, temp_manifest, temp_output_dir):
        """Test the full QC pipeline"""
        output_path = temp_output_dir / "post_qc_species_list.json"
        
        results = run_qc_pipeline(
            input_manifest_path=temp_manifest,
            output_path=output_path,
            min_replicates=2
        )
        
        # Verify output file was created
        assert output_path.exists()
        
        # Verify results structure
        assert "total_studies" in results
        assert "passed_count" in results
        assert "excluded_count" in results
        assert "excluded_species_list" in results
        
        # Verify counts
        assert results["total_studies"] == 4
        # SRP000001: valid (3 replicates, tissue=leaf)
        # SRP000002: excluded (1 replicate < 2)
        # SRP000003: excluded (tissue is empty)
        # SRP000004: valid (4 replicates, tissue=leaf)
        assert results["passed_count"] == 2
        assert results["excluded_count"] == 2
        
        # Verify excluded list content
        excluded_species = [item["species"] for item in results["excluded_species_list"]]
        assert "Zea mays" in excluded_species
        assert "Solanum lycopersicum" in excluded_species
        
        # Verify output file content
        with open(output_path, 'r') as f:
            output_data = json.load(f)
        
        assert len(output_data) == 2
        assert all("species" in item and "exclusion_reason" in item for item in output_data)

    def test_run_qc_pipeline_single_entry_manifest(self, temp_output_dir):
        """Test QC pipeline with a single entry manifest (not a list)"""
        manifest_data = {
            "accession_id": "SRP000005",
            "species": "Arabidopsis thaliana",
            "tissue": "root",
            "treatment": "herbivory",
            "replicates": 2
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(manifest_data, f)
            temp_path = Path(f.name)
        
        try:
            output_path = temp_output_dir / "post_qc_single.json"
            results = run_qc_pipeline(
                input_manifest_path=temp_path,
                output_path=output_path,
                min_replicates=2
            )
            
            assert results["total_studies"] == 1
            assert results["passed_count"] == 1
            assert results["excluded_count"] == 0
            assert output_path.exists()
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_run_qc_pipeline_missing_input(self, temp_output_dir):
        """Test QC pipeline with missing input manifest"""
        output_path = temp_output_dir / "post_qc_missing.json"
        missing_path = Path("nonexistent_manifest.json")
        
        with pytest.raises(FileNotFoundError):
            run_qc_pipeline(
                input_manifest_path=missing_path,
                output_path=output_path
            )