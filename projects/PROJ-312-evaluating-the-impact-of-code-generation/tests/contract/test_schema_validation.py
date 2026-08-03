import pytest
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import validate_json_schema

def test_pull_request_schema():
    schema_path = "contracts/pull_request.schema.yaml"
    
    valid_data = {
        "pr_id": "123",
        "repo_name": "test/repo",
        "created_at": "2023-01-01T00:00:00Z",
        "merged_at": "2023-01-02T00:00:00Z",
        "labels": [],
        "commit_messages": [],
        "turnaround_hours": 24.0
    }
    
    assert validate_json_schema(valid_data, schema_path) == True
    
    invalid_data = {
        "pr_id": "123",
        # missing repo_name
        "turnaround_hours": 24.0
    }
    
    assert validate_json_schema(invalid_data, schema_path) == False
