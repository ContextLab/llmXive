"""
Unit tests for schema contract validation.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from setup_schema_contracts import validate_yaml_schema, write_validation_log
from utils.exceptions import CorrosionPipelineError

class TestSchemaValidation:
    """Tests for schema validation functionality."""
    
    def test_ingest_schema_exists(self):
        """Test that ingest schema file exists and is valid YAML."""
        schema_path = "contracts/ingest.schema.yaml"
        full_path = PROJECT_ROOT / schema_path
        
        assert full_path.exists(), f"Schema file not found: {full_path}"
        
        import yaml
        with open(full_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        assert schema is not None, "Schema file is empty"
        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "alloy_id" in schema["properties"]
        
    def test_dataset_schema_exists(self):
        """Test that dataset schema file exists and is valid YAML."""
        schema_path = "contracts/dataset.schema.yaml"
        full_path = PROJECT_ROOT / schema_path
        
        assert full_path.exists(), f"Schema file not found: {full_path}"
        
        import yaml
        with open(full_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        assert schema is not None, "Schema file is empty"
        assert "properties" in schema
        assert "record_id" in schema["properties"]
        assert "potential_mV" in schema["properties"]
        
    def test_validate_yaml_schema_success(self):
        """Test validation of a valid schema file."""
        result = validate_yaml_schema("contracts/ingest.schema.yaml")
        
        assert "status" in result
        assert "details" in result
        assert result["status"] in ["PASS", "FAIL"]
        
    def test_validate_nonexistent_file(self):
        """Test validation of a nonexistent file raises error."""
        with pytest.raises(CorrosionPipelineError):
            validate_yaml_schema("contracts/nonexistent.schema.yaml")
            
    def test_validation_log_format(self):
        """Test that validation log is written in correct format."""
        # Create temporary directory for test
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily override PROJECT_ROOT behavior
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                # Create minimal schema file
                contracts_dir = Path(tmpdir) / "contracts"
                contracts_dir.mkdir()
                
                schema_content = """
                type: object
                properties:
                  test_field:
                    type: string
                """
                with open(contracts_dir / "test.schema.yaml", 'w') as f:
                    f.write(schema_content)
                
                # Run validation
                result = validate_yaml_schema("contracts/test.schema.yaml")
                result["schema_file"] = "contracts/test.schema.yaml"
                
                # Write log
                log_path = write_validation_log([result])
                
                assert log_path.exists()
                
                with open(log_path, 'r') as f:
                    log_data = json.load(f)
                
                assert "schema_file" in log_data
                assert "validation_timestamp" in log_data
                assert "status" in log_data
                assert "details" in log_data
                
            finally:
                os.chdir(original_cwd)
                
    def test_required_fields_in_ingest_schema(self):
        """Test that ingest schema has all required fields."""
        import yaml
        schema_path = PROJECT_ROOT / "contracts" / "ingest.schema.yaml"
        
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        required_fields = ["alloy_id", "composition", "specific_alloy_designation"]
        for field in required_fields:
            assert field in schema["properties"], f"Missing required field: {field}"
            
    def test_required_fields_in_dataset_schema(self):
        """Test that dataset schema has all required fields."""
        import yaml
        schema_path = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"
        
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        required_fields = [
            "record_id", "alloy_id", "specific_alloy_designation",
            "composition", "ph", "temperature", "electrolyte_type", "potential_mV"
        ]
        for field in required_fields:
            assert field in schema["properties"], f"Missing required field: {field}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
