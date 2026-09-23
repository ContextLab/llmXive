import pytest
import json
from pathlib import Path
import tempfile
import os

# Import the module under test
from verify_research import parse_research_md, validate_research_file

class TestResearchValidation:
    """Unit tests for research.md validation logic."""

    @pytest.fixture
    def temp_research_file(self, tmp_path):
        """Create a temporary research.md file for testing."""
        file_path = tmp_path / "research.md"
        return file_path

    def test_parse_static_urls(self, temp_research_file):
        """Test parsing of static, verified URLs."""
        content = """
        # Research Data Sources

        ## OpenML Dataset
        https://openml.org/api/v1/data/12345

        ## HuggingFace Dataset
        https://huggingface.co/datasets/example/lst-wear

        ## GitHub Raw File
        https://github.com/example/repo/blob/main/data.csv
        """
        temp_research_file.write_text(content)

        result = parse_research_md(temp_research_file)

        assert result["summary"]["total_sources"] == 3
        assert result["summary"]["static_sources"] == 3
        assert result["summary"]["unverified_sources"] == 0
        assert not result["dynamic_logic_found"]

    def test_parse_dynamic_logic_detection(self, temp_research_file):
        """Test detection of dynamic search logic."""
        content = """
        # Research Data Sources

        ## Dynamic Search
        https://example.com/search?q=laser+wear

        ## TODO Placeholder
        https://example.com/TODO/dataset

        ## Template Literal
        https://example.com/datasets/${dataset_id}
        """
        temp_research_file.write_text(content)

        result = parse_research_md(temp_research_file)

        assert result["dynamic_logic_found"] is True
        assert len(result["validation_errors"]) >= 3

    def test_parse_mixed_content(self, temp_research_file):
        """Test parsing of mixed static and dynamic content."""
        content = """
        # Research Data Sources

        ## Static Source
        https://openml.org/api/v1/data/67890

        ## Dynamic Source
        https://example.com/search?q=test

        ## Another Static Source
        https://doi.org/10.1234/example
        """
        temp_research_file.write_text(content)

        result = parse_research_md(temp_research_file)

        assert result["summary"]["total_sources"] == 3
        assert result["summary"]["static_sources"] == 2
        assert result["summary"]["unverified_sources"] == 1
        assert result["dynamic_logic_found"] is True

    def test_missing_file_raises_error(self, temp_research_file):
        """Test that missing file raises appropriate error."""
        temp_research_file.unlink()  # Remove the file

        with pytest.raises(FileNotFoundError):
            parse_research_md(temp_research_file)

    def test_validation_report_structure(self, temp_research_file):
        """Test that validation report has expected structure."""
        content = """
        # Research Data Sources
        https://openml.org/api/v1/data/11111
        """
        temp_research_file.write_text(content)

        result = parse_research_md(temp_research_file)

        # Check required keys
        assert "file_path" in result
        assert "total_lines" in result
        assert "data_sources" in result
        assert "dynamic_logic_found" in result
        assert "validation_errors" in result
        assert "warnings" in result
        assert "summary" in result

        # Check summary structure
        summary = result["summary"]
        assert "total_sources" in summary
        assert "static_sources" in summary
        assert "unverified_sources" in summary
        assert "dynamic_issues" in summary
        assert "warnings_count" in summary

    def test_doi_and_arxiv_parsing(self, temp_research_file):
        """Test parsing of DOI and arXiv references."""
        content = """
        # Research Data Sources

        ## DOI Reference
        doi:10.1016/j.wear.2023.123456

        ## arXiv Reference
        arxiv.org/abs/2301.12345
        """
        temp_research_file.write_text(content)

        result = parse_research_md(temp_research_file)

        # Both should be detected
        assert result["summary"]["total_sources"] == 2
        # DOIs are static, arXiv URLs might not match our pattern depending on format
        assert result["summary"]["static_sources"] >= 1

    def test_empty_file(self, temp_research_file):
        """Test parsing of empty file."""
        temp_research_file.write_text("")

        result = parse_research_md(temp_research_file)

        assert result["summary"]["total_sources"] == 0
        assert not result["dynamic_logic_found"]
        assert result["summary"]["dynamic_issues"] == 0

    def test_validation_output_file_creation(self, temp_research_file):
        """Test that validation creates output file."""
        content = """
        # Research Data Sources
        https://openml.org/api/v1/data/99999
        """
        temp_research_file.write_text(content)

        # Create temp output path
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_validation.json"

            # Temporarily override OUTPUT_PATH
            import verify_research
            original_output = verify_research.OUTPUT_PATH
            verify_research.OUTPUT_PATH = output_path

            try:
                result = validate_research_file(temp_research_file)

                assert output_path.exists()

                with open(output_path, 'r') as f:
                    saved_result = json.load(f)

                assert "summary" in saved_result
                assert saved_result["summary"]["total_sources"] == 1
            finally:
                verify_research.OUTPUT_PATH = original_output
