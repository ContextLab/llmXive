import pytest
import yaml
import json
from pathlib import Path
import jsonschema
from typing import Dict, Any

# Helper to load schema from YAML and convert to JSON Schema
def load_schema(path: str) -> Dict[str, Any]:
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def validate_instance(schema: Dict[str, Any], instance: Dict[str, Any]):
    # Basic validation logic since jsonschema might not be in deps
    # We will just check required fields exist for now
    if 'required' in schema:
        for field in schema['required']:
            assert field in instance, f"Missing required field: {field}"
    if 'properties' in schema:
        for key, value in instance.items():
            assert key in schema['properties'], f"Unexpected field: {key}"

class TestYAMLSchemas:
    @pytest.fixture
    def contracts_dir(self):
        return Path(__file__).parent.parent.parent / "contracts"

    def test_pr_data_schema_exists(self, contracts_dir):
        path = contracts_dir / "pr_data.yaml"
        assert path.exists(), "pr_data.yaml must exist"
        schema = load_schema(path)
        assert "properties" in schema
        assert "pr_id" in schema["properties"]

    def test_bug_detection_schema_exists(self, contracts_dir):
        path = contracts_dir / "bug_detection.yaml"
        assert path.exists(), "bug_detection.yaml must exist"
        schema = load_schema(path)
        assert "properties" in schema
        assert "severity" in schema["properties"]

    def test_alignment_result_schema_exists(self, contracts_dir):
        path = contracts_dir / "alignment_result.yaml"
        assert path.exists(), "alignment_result.yaml must exist"
        schema = load_schema(path)
        assert "properties" in schema
        assert "jaccard_index" in schema["properties"]

    def test_inference_request_schema_exists(self, contracts_dir):
        path = contracts_dir / "inference_request.yaml"
        assert path.exists(), "inference_request.yaml must exist"
        schema = load_schema(path)
        assert "properties" in schema
        assert "diff_content" in schema["properties"]

    def test_inference_response_schema_exists(self, contracts_dir):
        path = contracts_dir / "inference_response.yaml"
        assert path.exists(), "inference_response.yaml must exist"
        schema = load_schema(path)
        assert "properties" in schema
        assert "raw_output" in schema["properties"]

    def test_pr_data_schema_valid_fields(self, contracts_dir):
        schema = load_schema(contracts_dir / "pr_data.yaml")
        expected_fields = [
            "pr_id", "repo_name", "url", "title", "body", "created_at",
            "state", "author", "files_changed", "additions", "deletions",
            "linked_issue_ids", "review_comments", "diff_content"
        ]
        for field in expected_fields:
            assert field in schema["properties"], f"Missing field {field} in pr_data schema"

    def test_bug_detection_schema_valid_fields(self, contracts_dir):
        schema = load_schema(contracts_dir / "bug_detection.yaml")
        expected_fields = [
            "pr_id", "file_path", "line_start", "line_end", "severity",
            "description", "is_verified", "verification_method"
        ]
        for field in expected_fields:
            assert field in schema["properties"], f"Missing field {field} in bug_detection schema"

    def test_alignment_result_schema_valid_fields(self, contracts_dir):
        schema = load_schema(contracts_dir / "alignment_result.yaml")
        expected_fields = [
            "pr_id", "human_bug_index", "llm_bug_index", "match_type",
            "jaccard_index", "cosine_similarity", "file_path_match"
        ]
        for field in expected_fields:
            assert field in schema["properties"], f"Missing field {field} in alignment_result schema"

def test_yaml_syntax_validity(contracts_dir):
    """Ensure all YAML files are syntactically valid"""
    for yaml_file in contracts_dir.glob("*.yaml"):
        with open(yaml_file, 'r') as f:
            try:
                yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in {yaml_file}: {e}")