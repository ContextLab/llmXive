import pytest
import json
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.utils.error_handling import DataFetchError
from code.utils.data_sources_validator import validate_data_sources_config

class TestDataParsing:
    """Contract tests for data download validation."""

    def test_config_validation_pass(self, tmp_path):
        """Test that a valid config passes validation."""
        config_file = tmp_path / "data-sources.yaml"
        config_content = """
        sources:
          ml:
            cs.LG:
              url: http://export.arxiv.org/api/query
              limit: 100
          non_ml:
            Nature Climate Change:
              url: https://api.crossref.org/works
              dois:
                - "10.1038/s41558-020-00950-8"
              venue: "Nature Climate Change"
              acceptance_status: "accepted"
              domain: "Climate"
        """
        config_file.write_text(config_content)
        
        # Should not raise
        try:
            validate_data_sources_config(config_file)
        except Exception as e:
            pytest.fail(f"Valid config raised exception: {e}")

    def test_config_validation_missing_url(self, tmp_path):
        """Test that config missing URL fails."""
        config_file = tmp_path / "data-sources.yaml"
        config_content = """
        sources:
          ml:
            cs.LG:
              limit: 100
        """
        config_file.write_text(config_content)
        
        with pytest.raises(Exception):
            validate_data_sources_config(config_file)

    def test_config_validation_invalid_url_format(self, tmp_path):
        """Test that invalid URL format fails."""
        config_file = tmp_path / "data-sources.yaml"
        config_content = """
        sources:
          ml:
            cs.LG:
              url: not-a-valid-url
              limit: 100
        """
        config_file.write_text(config_content)
        
        with pytest.raises(Exception):
            validate_data_sources_config(config_file)

    def test_jsonl_parsing(self, tmp_path):
        """Test parsing of generated JSONL file."""
        test_data = [
            {"id": "1", "title": "Test", "abstract": "Valid abstract"},
            {"id": "2", "title": "Test2", "abstract": "Another abstract"}
        ]
        jsonl_file = tmp_path / "test.jsonl"
        
        with open(jsonl_file, 'w') as f:
            for entry in test_data:
                f.write(json.dumps(entry) + '\n')
        
        # Read back
        with open(jsonl_file, 'r') as f:
            loaded = [json.loads(line) for line in f]
        
        assert len(loaded) == 2
        assert loaded[0]['id'] == '1'
        assert loaded[1]['title'] == 'Test2'
