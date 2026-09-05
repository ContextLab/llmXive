"""
Unit tests for populate_sources.py
"""
import os
import sys
import pytest
import yaml
from pathlib import Path
import tempfile
import shutil

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.populate_sources import parse_verified_sources, save_sources_yaml


class TestParseVerifiedSources:
    """Tests for parse_verified_sources function"""
    
    def test_missing_file_raises_error(self):
        """Test that missing verified file raises ConfigurationError"""
        from utils.error_handlers import ConfigurationError
        
        with pytest.raises(ConfigurationError):
            parse_verified_sources(Path("/nonexistent/path.md"))
    
    def test_parse_with_valid_content(self):
        """Test parsing a valid research_verified.md content"""
        with tempfile.TemporaryDirectory() as tmpdir:
            verified_path = Path(tmpdir) / "research_verified.md"
            
            # Create a sample verified file
            sample_content = """
            # Verified Research Sources
            
            ## Data Sources
            - [Materials Project API](https://api.materialsproject.org/v2) - Official API endpoint
            - [NIST Alloy Database](https://www.nist.gov/alloys) - NIST reference data
            - [OpenAlloy](https://openalloy.org/api) - Open source alloy database
            
            ## Literature
            - [Solder Hardness Review](https://doi.org/10.1016/j.jallcom.2023.123456.pdf) - Comprehensive review
            - [Lead-Free Properties](https://link.springer.com/article/10.1007/s11664-022-09876-5.pdf) - Property analysis
            """
            
            verified_path.write_text(sample_content)
            
            # Parse the content
            result = parse_verified_sources(verified_path)
            
            # Verify structure
            assert "materials_project" in result
            assert "nist_uci" in result
            assert "openalloy" in result
            assert "literature_pdfs" in result
            
            # Verify URL updates
            assert result["materials_project"]["url"] == "https://api.materialsproject.org/v2"
            assert result["nist_uci"]["url"] == "https://www.nist.gov/alloys"
            assert result["openalloy"]["url"] == "https://openalloy.org/api"
            
            # Verify literature sources
            assert len(result["literature_pdfs"]) == 2
            assert result["literature_pdfs"][0]["name"] == "Solder Hardness Review"
            assert result["literature_pdfs"][0]["url"] == "https://doi.org/10.1016/j.jallcom.2023.123456.pdf"
    
    def test_empty_file_produces_defaults(self):
        """Test that an empty verified file produces default configuration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            verified_path = Path(tmpdir) / "research_verified.md"
            verified_path.write_text("# Verified Sources\n\nNo entries found.")
            
            result = parse_verified_sources(verified_path)
            
            # Should have defaults
            assert result["materials_project"]["url"] == "https://api.materialsproject.org"
            assert len(result["literature_pdfs"]) == 0


class TestSaveSourcesYaml:
    """Tests for save_sources_yaml function"""
    
    def test_save_and_reload(self):
        """Test that saved YAML can be reloaded correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "sources.yaml"
            
            test_config = {
                "test_source": {
                    "name": "Test",
                    "url": "https://test.com",
                    "type": "api"
                }
            }
            
            save_sources_yaml(test_config, output_path)
            
            assert output_path.exists()
            
            # Reload and verify
            with open(output_path, 'r') as f:
                loaded = yaml.safe_load(f)
            
            assert loaded == test_config
    
    def test_creates_parent_directories(self):
        """Test that parent directories are created if they don't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "deep" / "nested" / "path" / "sources.yaml"
            
            test_config = {"test": "data"}
            
            save_sources_yaml(test_config, output_path)
            
            assert output_path.exists()
            assert output_path.parent.exists()


class TestIntegration:
    """Integration tests for the full workflow"""
    
    def test_full_workflow(self):
        """Test the complete parse and save workflow"""
        with tempfile.TemporaryDirectory() as tmpdir:
            verified_path = Path(tmpdir) / "research_verified.md"
            output_path = Path(tmpdir) / "sources.yaml"
            
            # Create sample verified content
            sample_content = """
            # Verified Sources
            - [Test API](https://test.api.com/v1) - Test endpoint
            - [Paper PDF](https://example.com/paper.pdf) - Research paper
            """
            
            verified_path.write_text(sample_content)
            
            # Parse and save
            config = parse_verified_sources(verified_path)
            save_sources_yaml(config, output_path)
            
            # Verify output
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                saved_config = yaml.safe_load(f)
            
            assert saved_config["test_api"]["url"] == "https://test.api.com/v1"
            assert len(saved_config["literature_pdfs"]) == 1
            assert saved_config["literature_pdfs"][0]["url"] == "https://example.com/paper.pdf"
