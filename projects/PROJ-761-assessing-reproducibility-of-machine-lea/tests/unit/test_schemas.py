import json
import os
from pathlib import Path
import pytest

# Simple JSON schema validation without external deps if possible, 
# but standard practice usually involves jsonschema. 
# Since we cannot assume jsonschema is installed in the base environment 
# (only listed in requirements if needed), we will do basic structural checks
# or attempt import and skip if not available.

def validate_schema_structure(schema_path):
    """Basic validation that the file is valid JSON and has required keys."""
    with open(schema_path, 'r') as f:
        data = json.load(f)
    
    assert "$schema" in data, "Missing $schema key"
    assert "type" in data, "Missing type key"
    assert "properties" in data, "Missing properties key"
    return True

class TestSchemas:
    @pytest.fixture
    def contracts_dir(self):
        # Assume tests are run from project root or we find it
        base = Path(__file__).resolve().parent.parent.parent
        return base / "contracts"

    def test_paper_manifest_schema_exists(self, contracts_dir):
        path = contracts_dir / "PaperManifest.schema.json"
        assert path.exists(), "PaperManifest.schema.json not found"
        validate_schema_structure(path)

    def test_repro_result_schema_exists(self, contracts_dir):
        path = contracts_dir / "ReproResult.schema.json"
        assert path.exists(), "ReproResult.schema.json not found"
        validate_schema_structure(path)

    def test_stat_summary_schema_exists(self, contracts_dir):
        path = contracts_dir / "StatSummary.schema.json"
        assert path.exists(), "StatSummary.schema.json not found"
        validate_schema_structure(path)

    def test_paper_manifest_required_fields(self, contracts_dir):
        path = contracts_dir / "PaperManifest.schema.json"
        with open(path, 'r') as f:
            data = json.load(f)
        
        required = data.get("required", [])
        assert "doi" in required, "doi must be required"
        assert "repo_url" in required, "repo_url must be required"
        assert "dataset_name" in required, "dataset_name must be required"
        assert "reported_metrics" in required, "reported_metrics must be required"

    def test_repro_result_required_fields(self, contracts_dir):
        path = contracts_dir / "ReproResult.schema.json"
        with open(path, 'r') as f:
            data = json.load(f)
        
        required = data.get("required", [])
        assert "doi" in required, "doi must be required"
        assert "metrics" in required, "metrics must be required"
        assert "reproducibility_score" in required, "reproducibility_score must be required"