import pytest
import json
import tempfile
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from verify_research import parse_research_md, check_static_urls, validate_research_file

class TestResearchValidation:
    
    def test_parse_valid_research_md(self, tmp_path):
        """Test parsing a valid research.md file"""
        content = """
        # Research Data Sources

        | Source Name | Type | Verified | URL / ID |
        | :--- | :--- | :--- | :--- |
        | OpenML | Tabular | True | https://www.openml.org/api/v1/data/45678 |
        """
        file_path = tmp_path / "research.md"
        file_path.write_text(content)

        sources = parse_research_md(file_path)
        
        assert "OpenML" in sources
        assert sources["OpenML"]["verified"] is True
        assert "45678" in sources["OpenML"]["url_id"]

    def test_detect_dynamic_search_logic(self, tmp_path):
        """Test that dynamic search logic is detected"""
        content = """
        # Research Data Sources

        | Source Name | Type | Verified | URL / ID |
        | :--- | :--- | :--- | :--- |
        | Bad Source | Tabular | False | search('laser wear data') |
        """
        file_path = tmp_path / "research.md"
        file_path.write_text(content)

        sources = parse_research_md(file_path)
        errors = check_static_urls(sources)
        
        assert len(errors) > 0
        assert any("Dynamic search logic" in err for err in errors)

    def test_validate_file_passes(self, tmp_path):
        """Test that a valid file passes validation"""
        content = """
        # Research Data Sources

        | Source Name | Type | Verified | URL / ID |
        | :--- | :--- | :--- | :--- |
        | OpenML | Tabular | True | https://www.openml.org/api/v1/data/45678 |
        | HuggingFace | Tabular | True | datasets/materials-science/lst-wear-v1 |
        """
        file_path = tmp_path / "research.md"
        file_path.write_text(content)

        is_valid = validate_research_file(file_path)
        assert is_valid is True

    def test_validate_file_fails_on_missing_url(self, tmp_path):
        """Test that a file with missing URL fails"""
        content = """
        # Research Data Sources

        | Source Name | Type | Verified | URL / ID |
        | :--- | :--- | :--- | :--- |
        | Empty Source | Tabular | True | |
        """
        file_path = tmp_path / "research.md"
        file_path.write_text(content)

        is_valid = validate_research_file(file_path)
        assert is_valid is False