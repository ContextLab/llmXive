import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from validate.dry_run import check_file_exists, validate_schema_compliance, run_dry_run

class TestDryRun:
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_check_file_exists_positive(self, temp_dir):
        """Test that check_file_exists returns True for existing file."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        assert check_file_exists(str(test_file)) is True
    
    def test_check_file_exists_negative(self, temp_dir):
        """Test that check_file_exists returns False for missing file."""
        missing_file = temp_dir / "nonexistent.txt"
        
        assert check_file_exists(str(missing_file)) is False
    
    def test_validate_schema_compliance_valid(self, temp_dir):
        """Test schema validation with valid data."""
        # Create schema file
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["scene_id", "constraints", "status"],
            "properties": {
                "scene_id": {"type": "string"},
                "constraints": {"type": "array"},
                "status": {"type": "string"}
            }
        }
        schema_file = temp_dir / "schema.yaml"
        with open(schema_file, 'w') as f:
            yaml.dump(schema, f)
        
        # Create valid JSONL file
        jsonl_file = temp_dir / "valid.jsonl"
        valid_records = [
            {"scene_id": "scene_001", "constraints": [{"type": "left_of", "a": "obj1", "b": "obj2"}], "status": "valid"},
            {"scene_id": "scene_002", "constraints": [{"type": "above", "a": "obj3", "b": "obj4"}], "status": "valid"}
        ]
        with open(jsonl_file, 'w') as f:
            for record in valid_records:
                f.write(json.dumps(record) + "\n")
        
        assert validate_schema_compliance(str(jsonl_file), str(schema_file)) is True
    
    def test_validate_schema_compliance_invalid(self, temp_dir):
        """Test schema validation with invalid data."""
        # Create schema file
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["scene_id", "constraints", "status"],
            "properties": {
                "scene_id": {"type": "string"},
                "constraints": {"type": "array"},
                "status": {"type": "string"}
            }
        }
        schema_file = temp_dir / "schema.yaml"
        with open(schema_file, 'w') as f:
            yaml.dump(schema, f)
        
        # Create invalid JSONL file (missing required field)
        jsonl_file = temp_dir / "invalid.jsonl"
        invalid_record = {"scene_id": "scene_001"}  # Missing constraints and status
        with open(jsonl_file, 'w') as f:
            f.write(json.dumps(invalid_record) + "\n")
        
        assert validate_schema_compliance(str(jsonl_file), str(schema_file)) is False
    
    def test_run_dry_run_success(self, temp_dir):
        """Test complete dry-run with valid data."""
        # Create schema file
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["scene_id", "constraints", "status"],
            "properties": {
                "scene_id": {"type": "string"},
                "constraints": {"type": "array"},
                "status": {"type": "string"}
            }
        }
        schema_file = temp_dir / "schema.yaml"
        with open(schema_file, 'w') as f:
            yaml.dump(schema, f)
        
        # Create valid JSONL file
        jsonl_file = temp_dir / "constraints.jsonl"
        valid_record = {"scene_id": "scene_001", "constraints": [{"type": "left_of", "a": "obj1", "b": "obj2"}], "status": "valid"}
        with open(jsonl_file, 'w') as f:
            f.write(json.dumps(valid_record) + "\n")
        
        output_file = temp_dir / "dry_run_status.json"
        
        success = run_dry_run(str(jsonl_file), str(schema_file), str(output_file))
        
        assert success is True
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            results = json.load(f)
        
        assert results["status"] == "pass"
        assert results["checks"]["file_exists"] is True
        assert results["checks"]["schema_exists"] is True
        assert results["checks"]["schema_compliance"] is True
    
    def test_run_dry_run_failure(self, temp_dir):
        """Test complete dry-run with missing input file."""
        schema_file = temp_dir / "schema.yaml"
        schema_file.write_text("test")
        
        missing_file = temp_dir / "missing.jsonl"
        output_file = temp_dir / "dry_run_status.json"
        
        success = run_dry_run(str(missing_file), str(schema_file), str(output_file))
        
        assert success is False
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            results = json.load(f)
        
        assert results["status"] == "fail"
        assert results["checks"]["file_exists"] is False
        assert len(results["errors"]) > 0