import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from utils import validate_json_schema


class TestSchemaValidation:
    """Contract tests for schema validation"""

    @pytest.fixture
    def valid_pr_data(self):
        return {
            "pr_id": "PR-123",
            "repo_name": "test/repo",
            "created_at": "2023-01-01T00:00:00Z",
            "merged_at": "2023-01-02T00:00:00Z",
            "labels": ["bug", "ai-generated"],
            "commit_messages": ["Fix bug", "AI generated code"],
            "turnaround_hours": 24.0
        }

    @pytest.fixture
    def invalid_pr_data(self):
        # Missing required field 'turnaround_hours'
        return {
            "pr_id": "PR-123",
            "repo_name": "test/repo",
            "created_at": "2023-01-01T00:00:00Z",
            "merged_at": "2023-01-02T00:00:00Z",
            "labels": ["bug"],
            "commit_messages": ["Fix bug"]
        }

    def test_valid_pr_schema(self, valid_pr_data):
        """Test that valid PR data passes schema validation"""
        schema_path = "contracts/pull_request.schema.yaml"
        assert validate_json_schema(valid_pr_data, schema_path) is True

    def test_invalid_pr_schema(self, invalid_pr_data):
        """Test that invalid PR data fails schema validation"""
        schema_path = "contracts/pull_request.schema.yaml"
        assert validate_json_schema(invalid_pr_data, schema_path) is False

    def test_repo_metadata_schema(self):
        """Test repo metadata schema validation"""
        schema_path = "contracts/repo_metadata.schema.yaml"
        
        valid_data = {
            "repo_name": "test/repo",
            "stars": 50000,
            "contributors": 100
        }
        
        invalid_data = {
            "repo_name": "test/repo"
            # Missing required 'stars'
        }
        
        assert validate_json_schema(valid_data, schema_path) is True
        assert validate_json_schema(invalid_data, schema_path) is False

    def test_statistical_result_schema(self):
        """Test statistical result schema validation"""
        schema_path = "contracts/statistical_result.schema.yaml"
        
        valid_data = {
            "test_type": "mann_whitney_u",
            "u_statistic": 1234.5,
            "p_value": 0.03,
            "effect_size": 0.45,
            "sample_sizes": {"ai": 50, "non_ai": 100}
        }
        
        invalid_data = {
            "test_type": "mann_whitney_u"
            # Missing required 'u_statistic' and 'p_value'
        }
        
        assert validate_json_schema(valid_data, schema_path) is True
        assert validate_json_schema(invalid_data, schema_path) is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])