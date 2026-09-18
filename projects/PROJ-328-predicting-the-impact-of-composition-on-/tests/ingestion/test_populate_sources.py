"""
Tests for T009c: populate_sources.py
"""
import os
import sys
import yaml
import tempfile
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.ingestion.populate_sources import parse_verified_sources, save_sources_yaml


class TestPopulateSources:
    """Test suite for source population logic."""

    def test_parse_verified_md(self, tmp_path):
        """Test parsing of research_verified.md format."""
        # Create a mock verified file
        mock_content = """
        ## Verified Sources

        ### API Sources
        - [https://api.materialsproject.org] Materials Project API
        - [https://archive.ics.uci.edu] NIST/UCI Repository

        ### Literature
        - [https://doi.org/10.1016/j.jallcom.2023.123456] Solder Hardness Review 2023
        """
        mock_file = tmp_path / "research_verified.md"
        mock_file.write_text(mock_content)

        # Parse sources
        sources = parse_verified_sources(mock_file)

        # Verify structure
        assert "_verification_status" in sources
        assert sources["_verification_status"] == "verified"
        assert sources["_verified_count"] >= 1
        assert "materials_project" in sources
        assert "literature_pdfs" in sources

    def test_parse_candidate_json(self, tmp_path):
        """Test parsing of candidate_sources.txt JSON format."""
        import json
        mock_content = json.dumps([
            {
                "url": "https://api.materialsproject.org",
                "source_type": "api",
                "citation": "Materials Project"
            },
            {
                "url": "https://doi.org/10.1016/j.jallcom.2023.123456",
                "source_type": "pdf",
                "citation": "Solder Hardness Review"
            }
        ])
        mock_file = tmp_path / "candidate_sources.txt"
        mock_file.write_text(mock_content)

        # Parse sources
        sources = parse_verified_sources(mock_file)

        # Verify structure
        assert "_verification_status" in sources
        assert "materials_project" in sources
        assert "literature_pdfs" in sources

    def test_save_sources_yaml(self, tmp_path):
        """Test saving sources to YAML."""
        sources = {
            "_verification_status": "verified",
            "_verified_count": 1,
            "test_source": {
                "name": "Test",
                "url": "https://example.com",
                "verified": True
            }
        }
        output_file = tmp_path / "sources.yaml"

        # Save sources
        save_sources_yaml(sources, output_file)

        # Verify file exists and is valid YAML
        assert output_file.exists()
        with open(output_file, 'r') as f:
            loaded = yaml.safe_load(f)
        
        assert loaded["_verification_status"] == "verified"
        assert loaded["test_source"]["url"] == "https://example.com"

    def test_missing_input_file(self, tmp_path):
        """Test error handling for missing input file."""
        from utils.error_handlers import ConfigurationError
        
        non_existent = tmp_path / "does_not_exist.md"
        
        with pytest.raises(ConfigurationError):
            parse_verified_sources(non_existent)
