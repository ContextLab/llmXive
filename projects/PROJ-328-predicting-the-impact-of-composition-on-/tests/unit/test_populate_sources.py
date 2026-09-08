"""
Unit tests for T009c: Populate sources.yaml
"""
import os
import sys
import pytest
import yaml
from pathlib import Path
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from ingestion.populate_sources import parse_verified_sources, save_sources_yaml
from utils.error_handlers import ConfigurationError


class TestParseVerifiedSources:
    """Tests for parse_verified_sources function"""

    def test_file_not_found_raises_error(self, tmp_path):
        """Test that missing verified file raises ConfigurationError"""
        fake_path = tmp_path / "non_existent.md"
        
        with pytest.raises(ConfigurationError) as exc_info:
            parse_verified_sources(fake_path)
        
        assert "not found" in str(exc_info.value).lower()

    def test_empty_file_raises_error(self, tmp_path):
        """Test that empty file raises ConfigurationError"""
        empty_file = tmp_path / "empty.md"
        empty_file.write_text("")
        
        with pytest.raises(ConfigurationError) as exc_info:
            parse_verified_sources(empty_file)
        
        assert "no valid sources" in str(exc_info.value).lower()

    def test_parses_materials_project_url(self, tmp_path):
        """Test extraction of Materials Project URL"""
        content = """
        # Materials Project
        Visit https://api.materialsproject.org for data access.
        """
        test_file = tmp_path / "test.md"
        test_file.write_text(content)
        
        sources = parse_verified_sources(test_file)
        
        assert sources['materials_project'].get('url') == "https://api.materialsproject.org"
        assert sources['materials_project'].get('verified') is True

    def test_parses_nist_uci_url(self, tmp_path):
        """Test extraction of NIST/UCI URL"""
        content = """
        ## NIST Repository
        Data available at https://archive.ics.uci.edu/ml/datasets.php
        """
        test_file = tmp_path / "test.md"
        test_file.write_text(content)
        
        sources = parse_verified_sources(test_file)
        
        assert sources['nist_uci'].get('url') == "https://archive.ics.uci.edu/ml/datasets.php"
        assert sources['nist_uci'].get('verified') is True

    def test_parses_openalloy_url(self, tmp_path):
        """Test extraction of OpenAlloy URL"""
        content = """
        # OpenAlloy Database
        API: https://openalloy.org/api/v1
        """
        test_file = tmp_path / "test.md"
        test_file.write_text(content)
        
        sources = parse_verified_sources(test_file)
        
        assert sources['openalloy'].get('url') == "https://openalloy.org/api/v1"
        assert sources['openalloy'].get('verified') is True

    def test_parses_literature_pdfs(self, tmp_path):
        """Test extraction of literature PDF sources"""
        content = """
        # Literature Review
        **Solder Hardness Review 2023** https://doi.org/10.1016/j.jallcom.2023.123456
        **Lead-Free Solder Properties** https://doi.org/10.1007/s11664-022-09876-5
        """
        test_file = tmp_path / "test.md"
        test_file.write_text(content)
        
        sources = parse_verified_sources(test_file)
        
        assert len(sources['literature_pdfs']) == 2
        assert sources['literature_pdfs'][0]['name'] == "Solder Hardness Review 2023"
        assert sources['literature_pdfs'][1]['name'] == "Lead-Free Solder Properties"
        assert sources['literature_pdfs'][0]['format'] == "pdf"
        assert sources['literature_pdfs'][0]['verified'] is True

    def test_parses_mixed_sources(self, tmp_path):
        """Test extraction of multiple source types"""
        content = """
        # Materials Project
        https://api.materialsproject.org

        ## NIST
        https://archive.ics.uci.edu

        # OpenAlloy
        https://openalloy.org/api

        ## Literature
        **Paper 1** https://doi.org/10.1234/test
        """
        test_file = tmp_path / "test.md"
        test_file.write_text(content)
        
        sources = parse_verified_sources(test_file)
        
        assert sources['materials_project'].get('url') is not None
        assert sources['nist_uci'].get('url') is not None
        assert sources['openalloy'].get('url') is not None
        assert len(sources['literature_pdfs']) == 1

class TestSaveSourcesYaml:
    """Tests for save_sources_yaml function"""

    def test_creates_yaml_file(self, tmp_path):
        """Test that function creates a valid YAML file"""
        sources = {
            'materials_project': {'url': 'https://test.com', 'verified': True},
            'nist_uci': {'url': 'https://test.com', 'verified': True},
            'openalloy': {'url': 'https://test.com', 'verified': True},
            'literature_pdfs': []
        }
        
        output_path = tmp_path / "sources.yaml"
        save_sources_yaml(sources, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            data = yaml.safe_load(f)
        
        assert 'materials_project' in data
        assert 'nist_uci' in data
        assert 'openalloy' in data
        assert 'literature_pdfs' in data

    def test_yaml_structure_valid(self, tmp_path):
        """Test that the generated YAML has correct structure"""
        sources = {
            'materials_project': {'url': 'https://mp.com', 'verified': True},
            'nist_uci': {'url': 'https://nist.com', 'verified': True},
            'openalloy': {'url': 'https://open.com', 'verified': True},
            'literature_pdfs': [
                {'name': 'Test Paper', 'url': 'https://doi.org/10.1234/test'}
            ]
        }
        
        output_path = tmp_path / "sources.yaml"
        save_sources_yaml(sources, output_path)
        
        with open(output_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Check nested structure
        assert data['materials_project']['url'] == 'https://mp.com'
        assert data['nist_uci']['url'] == 'https://nist.com'
        assert data['openalloy']['url'] == 'https://open.com'
        assert len(data['literature_pdfs']) == 1
        assert data['literature_pdfs'][0]['name'] == 'Test Paper'

class TestIntegration:
    """Integration tests for the full T009c workflow"""

    def test_full_workflow(self, tmp_path):
        """Test complete workflow from verified markdown to sources.yaml"""
        # Create a realistic verified research file
        content = """
        # Research Verification Report

        ## Materials Project
        Verified URL: https://api.materialsproject.org/v4

        ## NIST/UCI
        Repository: https://archive.ics.uci.edu/ml/datasets/solder

        ## OpenAlloy
        API Endpoint: https://openalloy.org/api/v1/compositions

        ## Literature Sources
        **Comprehensive Review** https://doi.org/10.1016/j.matchar.2023.112345
        **Experimental Study** https://doi.org/10.1007/s11837-022-05432-1
        """
        
        verified_file = tmp_path / "research_verified.md"
        verified_file.write_text(content)
        
        output_dir = tmp_path / "data" / "config"
        output_file = output_dir / "sources.yaml"
        
        # Parse and save
        sources = parse_verified_sources(verified_file)
        save_sources_yaml(sources, output_file)
        
        # Verify output
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            data = yaml.safe_load(f)
        
        # Verify all sections are populated
        assert data['materials_project']['url'] == "https://api.materialsproject.org/v4"
        assert data['nist_uci']['url'] == "https://archive.ics.uci.edu/ml/datasets/solder"
        assert data['openalloy']['url'] == "https://openalloy.org/api/v1/compositions"
        assert len(data['literature_pdfs']) == 2
        
        # Verify no placeholder comments remain
        with open(output_file, 'r') as f:
            content = f.read()
        
        assert "placeholder" not in content.lower()
        assert "will be replaced" not in content.lower()