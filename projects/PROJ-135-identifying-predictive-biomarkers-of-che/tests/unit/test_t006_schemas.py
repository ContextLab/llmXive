"""
Unit tests for T006: Schema generation and validation.
"""
import os
import sys
import yaml
import tempfile
import json
from pathlib import Path
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.schema_manager import SCHEMAS, compute_sha256, write_schemas, update_state_with_schema_checksums
from code.src.config import get_project_root

class TestSchemaDefinitions:
    """Tests for the in-memory schema definitions."""

    def test_schema_keys_exist(self):
        """Verify all required schema files are defined."""
        assert "dataset.schema.yaml" in SCHEMAS
        assert "model_output.schema.yaml" in SCHEMAS
        assert "meta_analysis.schema.yaml" in SCHEMAS

    def test_dataset_schema_structure(self):
        """Verify dataset schema has required fields."""
        schema = SCHEMAS["dataset.schema.yaml"]
        assert schema["type"] == "object"
        required_fields = ["sample_id", "tumor_type", "response_label", "expression_vector"]
        for field in required_fields:
            assert field in schema["required"]
            assert field in schema["properties"]

    def test_model_output_schema_structure(self):
        """Verify model output schema has required fields."""
        schema = SCHEMAS["model_output.schema.yaml"]
        required_fields = ["cancer_type", "alpha", "lambda", "coefficients", "cross_val_auc"]
        for field in required_fields:
            assert field in schema["required"]
            assert field in schema["properties"]

    def test_meta_analysis_schema_structure(self):
        """Verify meta analysis schema has required fields."""
        schema = SCHEMAS["meta_analysis.schema.yaml"]
        required_fields = ["gene_symbol", "meta_p_value", "log2FC_mean", "selected"]
        for field in required_fields:
            assert field in schema["required"]
            assert field in schema["properties"]

class TestSchemaWriting:
    """Tests for schema file writing functionality."""

    @pytest.fixture
    def temp_contract_dir(self, tmp_path):
        """Create a temporary contracts directory."""
        contracts_dir = tmp_path / "specs" / "001-chemo-biomarker-discovery" / "contracts"
        contracts_dir.mkdir(parents=True)
        return contracts_dir

    def test_write_schemas_creates_files(self, temp_contract_dir):
        """Verify write_schemas creates all expected files."""
        # Temporarily override the contract directory for testing
        original_schemas = SCHEMAS.copy()
        
        # Mock get_project_root to return temp directory
        import code.src.schema_manager as sm
        original_get_root = sm.get_project_root
        sm.get_project_root = lambda: temp_contract_dir.parent.parent.parent
        
        try:
            checksums = write_schemas()
            assert len(checksums) == 3
            
            for filename in SCHEMAS.keys():
                file_path = temp_contract_dir / filename
                assert file_path.exists(), f"File {filename} was not created"
                
                # Verify file is valid YAML
                with open(file_path, 'r') as f:
                    loaded = yaml.safe_load(f)
                    assert loaded is not None
        finally:
            sm.get_project_root = original_get_root

    def test_checksums_are_valid_sha256(self, temp_contract_dir):
        """Verify generated checksums are valid SHA256 hashes."""
        import code.src.schema_manager as sm
        sm.get_project_root = lambda: temp_contract_dir.parent.parent.parent
        
        try:
            checksums = write_schemas()
            for filename, checksum in checksums.items():
                assert len(checksum) == 64, f"Checksum for {filename} is not 64 chars"
                assert all(c in '0123456789abcdef' for c in checksum), f"Checksum for {filename} contains non-hex chars"
        finally:
            pass # Restore not needed as we replaced with lambda

class TestStateUpdate:
    """Tests for state file update functionality."""

    def test_state_update_creates_file(self, tmp_path):
        """Verify update_state_with_schema_checksums creates state file."""
        state_dir = tmp_path / "state" / "projects"
        state_dir.mkdir(parents=True)
        
        # Mock get_project_root
        import code.src.schema_manager as sm
        original_get_root = sm.get_project_root
        sm.get_project_root = lambda: tmp_path
        
        try:
            test_checksums = {
                "test.schema.yaml": "a" * 64,
                "test2.schema.yaml": "b" * 64
            }
            
            update_state_with_schema_checksums(test_checksums)
            
            state_file = state_dir / "PROJ-135-identifying-predictive-biomarkers-of-che.yaml"
            assert state_file.exists()
            
            with open(state_file, 'r') as f:
                state_data = yaml.safe_load(f)
            
            assert "artifact_hashes" in state_data
            assert "test.schema.yaml" in state_data["artifact_hashes"]
            assert "test2.schema.yaml" in state_data["artifact_hashes"]
        finally:
            sm.get_project_root = original_get_root

class TestIntegration:
    """Integration tests for the full T006 workflow."""

    def test_full_workflow(self, tmp_path):
        """Test the complete T006 workflow: write -> checksum -> state update."""
        # Setup
        contracts_dir = tmp_path / "specs" / "001-chemo-biomarker-discovery" / "contracts"
        contracts_dir.mkdir(parents=True)
        state_dir = tmp_path / "state" / "projects"
        state_dir.mkdir(parents=True)
        
        import code.src.schema_manager as sm
        sm.get_project_root = lambda: tmp_path
        
        try:
            # Execute
            checksums = write_schemas()
            update_state_with_schema_checksums(checksums)
            
            # Verify schemas exist and are valid
            for filename in SCHEMAS.keys():
                file_path = contracts_dir / filename
                assert file_path.exists()
                with open(file_path, 'r') as f:
                    loaded = yaml.safe_load(f)
                    assert loaded["title"] == SCHEMAS[filename]["title"]
            
            # Verify state file
            state_file = state_dir / "PROJ-135-identifying-predictive-biomarkers-of-che.yaml"
            assert state_file.exists()
            with open(state_file, 'r') as f:
                state_data = yaml.safe_load(f)
            
            assert len(state_data["artifact_hashes"]) >= 3
        finally:
            pass