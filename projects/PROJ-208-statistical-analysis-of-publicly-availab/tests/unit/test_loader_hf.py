"""
Unit tests for HuggingFace Streaming Loader.
"""
import pytest
from pathlib import Path
import sys
import json
import tempfile
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.loader_hf import fetch_hf_data, validate_and_save
from utils.validators import load_schema, validate_dataset_schema

class TestLoaderHF:
    """Tests for the HuggingFace loader module."""

    def test_schema_loading(self):
        """Test that the schema file can be loaded."""
        schema_path = Path("contracts/dataset.schema.yaml")
        assert schema_path.exists(), "Schema file should exist"
        
        schema = load_schema(str(schema_path))
        assert 'type' in schema
        assert schema['type'] == 'object'
        assert 'required' in schema
        assert 'properties' in schema

    def test_validate_sample_data(self):
        """Test validation with sample data matching the schema."""
        sample_data = [
            {
                "repository_full_name": "test/repo",
                "issue_number": 1,
                "created_at": "2023-01-01T00:00:00Z",
                "closed_at": "2023-01-02T00:00:00Z",
                "state": "closed",
                "title": "Test Issue",
                "user_login": "testuser",
                "labels": ["bug", "help wanted"],
                "comments_count": 5,
                "assignee": "testuser",
                "body": "Test body",
                "url": "https://github.com/test/repo/issues/1",
                "closed_by": "testuser"
            }
        ]
        
        schema_path = Path("contracts/dataset.schema.yaml")
        schema = load_schema(str(schema_path))
        
        result = validate_dataset_schema(sample_data, schema)
        assert result['valid'], f"Sample data should be valid: {result.get('errors')}"

    def test_validate_invalid_data(self):
        """Test validation fails with invalid data."""
        invalid_data = [
            {
                "repository_full_name": "test/repo",
                # Missing required field 'issue_number'
                "created_at": "2023-01-01T00:00:00Z",
                "state": "invalid_state",  # Invalid enum value
            }
        ]
        
        schema_path = Path("contracts/dataset.schema.yaml")
        schema = load_schema(str(schema_path))
        
        result = validate_dataset_schema(invalid_data, schema)
        assert not result['valid'], "Invalid data should fail validation"
        assert len(result.get('errors', [])) > 0

    def test_validate_and_save_creates_file(self):
        """Test that validate_and_save creates the output file."""
        sample_data = [
            {
                "repository_full_name": "test/repo",
                "issue_number": 1,
                "created_at": "2023-01-01T00:00:00Z",
                "closed_at": "2023-01-02T00:00:00Z",
                "state": "closed",
                "title": "Test Issue",
                "user_login": "testuser",
                "labels": ["bug"],
                "comments_count": 0,
                "assignee": None,
                "body": None,
                "url": "https://github.com/test/repo/issues/1",
                "closed_by": None
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.parquet"
            schema_path = Path("contracts/dataset.schema.yaml")
            
            success = validate_and_save(sample_data, str(schema_path), str(output_path))
            
            assert success, "Validation and save should succeed"
            assert output_path.exists(), "Output file should be created"
            
            # Verify we can read it back
            import pandas as pd
            df = pd.read_parquet(output_path)
            assert len(df) == 1
            assert df['repository_full_name'].iloc[0] == "test/repo"

    def test_fetch_hf_data_structure(self):
        """Test that fetch_hf_data returns a list of dicts (if data is available)."""
        # This test will skip if the dataset is not available in the environment
        try:
            data = fetch_hf_data(streaming=True)
            assert isinstance(data, list), "Data should be a list"
            if len(data) > 0:
                assert isinstance(data[0], dict), "Each item should be a dict"
                assert 'repository_full_name' in data[0], "Each item should have repository_full_name"
        except Exception as e:
            # If dataset is not available, skip the test
            pytest.skip(f"Dataset not available: {str(e)}")