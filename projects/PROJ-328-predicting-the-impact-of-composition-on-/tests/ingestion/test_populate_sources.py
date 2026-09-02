"""
Tests for T009c: Populate sources.yaml from research_verified.md.
"""

import os
import sys
import pytest
import yaml
from pathlib import Path
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ingestion.populate_sources import parse_verified_sources, save_sources_yaml
from utils.error_handlers import ConfigurationError


class TestPopulateSources:
    """Test suite for populate_sources.py"""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        temp_base = tempfile.mkdtemp()
        specs_dir = Path(temp_base) / "specs" / "001-predict-solder-hardness"
        specs_dir.mkdir(parents=True)
        
        data_dir = Path(temp_base) / "data" / "config"
        data_dir.mkdir(parents=True)

        yield {
            "base": temp_base,
            "specs": specs_dir,
            "data": data_dir
        }

        # Cleanup
        shutil.rmtree(temp_base)

    def test_parse_missing_file_raises_error(self, temp_dirs):
        """Test that parsing a missing file raises ConfigurationError."""
        missing_path = temp_dirs["specs"] / "nonexistent.md"
        
        with pytest.raises(ConfigurationError) as exc_info:
            parse_verified_sources(missing_path)
        
        assert "not found" in str(exc_info.value)

    def test_parse_empty_file_raises_error(self, temp_dirs):
        """Test that parsing an empty file raises ConfigurationError."""
        empty_file = temp_dirs["specs"] / "research_verified.md"
        empty_file.write_text("")

        with pytest.raises(ConfigurationError) as exc_info:
            parse_verified_sources(empty_file)
        
        assert "No verified sources found" in str(exc_info.value)

    def test_parse_with_materials_project_url(self, temp_dirs):
        """Test parsing a file with a Materials Project URL."""
        verified_file = temp_dirs["specs"] / "research_verified.md"
        content = """
        # Verified Research Sources

        ## Materials Project
        - URL: https://api.materialsproject.org/v4/
        - Status: Verified
        """
        verified_file.write_text(content)

        sources = parse_verified_sources(verified_file)

        assert sources["materials_project"]["verified"] is True
        assert sources["materials_project"]["url"] == "https://api.materialsproject.org/v4/"

    def test_parse_with_nist_uci_url(self, temp_dirs):
        """Test parsing a file with a NIST/UCI URL."""
        verified_file = temp_dirs["specs"] / "research_verified.md"
        content = """
        # Verified Research Sources

        ## NIST/UCI Repository
        - URL: https://archive.ics.uci.edu/ml/datasets/Solder
        - Status: Verified
        """
        verified_file.write_text(content)

        sources = parse_verified_sources(verified_file)

        assert sources["nist_uci"]["verified"] is True
        assert "archive.ics.uci.edu" in sources["nist_uci"]["url"]

    def test_parse_with_openalloy_url(self, temp_dirs):
        """Test parsing a file with an OpenAlloy URL."""
        verified_file = temp_dirs["specs"] / "research_verified.md"
        content = """
        # Verified Research Sources

        ## OpenAlloy Database
        - URL: https://openalloy.org/api/v1/compositions
        - Status: Verified
        """
        verified_file.write_text(content)

        sources = parse_verified_sources(verified_file)

        assert sources["openalloy"]["verified"] is True
        assert "openalloy.org" in sources["openalloy"]["url"]

    def test_parse_with_doi_literature(self, temp_dirs):
        """Test parsing a file with DOI links for literature."""
        verified_file = temp_dirs["specs"] / "research_verified.md"
        content = """
        # Verified Research Sources

        ## Literature
        - Solder Hardness Review 2023: https://doi.org/10.1016/j.jallcom.2023.123456
        - Lead-Free Solder Properties: https://doi.org/10.1007/s11664-022-09876-5
        """
        verified_file.write_text(content)

        sources = parse_verified_sources(verified_file)

        assert len(sources["literature_pdfs"]) == 2
        assert "doi.org/10.1016" in sources["literature_pdfs"][0]["url"]
        assert "doi.org/10.1007" in sources["literature_pdfs"][1]["url"]
        assert sources["literature_pdfs"][0]["format"] == "pdf"

    def test_save_sources_yaml_creates_file(self, temp_dirs):
        """Test that save_sources_yaml creates the file correctly."""
        sources = {
            "materials_project": {
                "name": "Materials Project",
                "type": "api",
                "url": "https://api.materialsproject.org",
                "verified": True
            },
            "literature_pdfs": [
                {
                    "name": "Test Paper",
                    "url": "https://doi.org/10.1234/test",
                    "format": "pdf",
                    "verified": True
                }
            ]
        }

        output_path = temp_dirs["data"] / "sources.yaml"
        save_sources_yaml(sources, output_path)

        assert output_path.exists()

        # Verify YAML is valid
        with open(output_path, 'r') as f:
            loaded = yaml.safe_load(f)

        assert loaded["materials_project"]["url"] == "https://api.materialsproject.org"
        assert len(loaded["literature_pdfs"]) == 1

    def test_integration_parse_and_save(self, temp_dirs):
        """Integration test: parse a verified file and save to YAML."""
        # Create verified file
        verified_file = temp_dirs["specs"] / "research_verified.md"
        content = """
        # Verified Research Sources

        ## Materials Project
        - URL: https://api.materialsproject.org/v4/
        
        ## Literature
        - Test Paper: https://doi.org/10.1016/test.pdf
        """
        verified_file.write_text(content)

        # Parse
        sources = parse_verified_sources(verified_file)

        # Save
        output_path = temp_dirs["data"] / "sources.yaml"
        save_sources_yaml(sources, output_path)

        # Verify
        assert output_path.exists()
        with open(output_path, 'r') as f:
            loaded = yaml.safe_load(f)

        assert loaded["materials_project"]["verified"] is True
        assert len(loaded["literature_pdfs"]) == 1
