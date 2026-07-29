"""
Unit tests for URL validation module.
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.utils.validate_urls import (
    parse_research_manifest,
    validate_url_pattern,
    validate_dataset_urls,
    validate_urls
)


class TestParseResearchManifest:
    """Tests for parse_research_manifest function."""

    def test_valid_manifest_parsing(self, tmp_path):
        """Test parsing a valid research.md file."""
        manifest_content = """
        # Research Manifest

        ### VulDeePecker
        - https://github.com/example/vuldeepecker
        - https://example.com/vuldeepecker/dataset.zip

        ### BigVul
        - https://github.com/example/bigvul
        """
        manifest_file = tmp_path / "research.md"
        manifest_file.write_text(manifest_content)

        result = parse_research_manifest(manifest_file)

        assert "VulDeePecker" in result
        assert "BigVul" in result
        assert len(result["VulDeePecker"]) == 2
        assert len(result["BigVul"]) == 1

    def test_missing_manifest_file(self, tmp_path):
        """Test handling of missing manifest file."""
        non_existent = tmp_path / "non_existent.md"

        with pytest.raises(FileNotFoundError):
            parse_research_manifest(non_existent)

    def test_empty_manifest(self, tmp_path):
        """Test parsing an empty manifest file."""
        manifest_file = tmp_path / "research.md"
        manifest_file.write_text("")

        result = parse_research_manifest(manifest_file)
        assert result == {}

    def test_inline_url_pattern(self, tmp_path):
        """Test parsing inline URL patterns."""
        manifest_content = """
        # Research Manifest

        VulDeePecker: https://github.com/example/vuldeepecker
        BigVul: https://github.com/example/bigvul
        """
        manifest_file = tmp_path / "research.md"
        manifest_file.write_text(manifest_content)

        result = parse_research_manifest(manifest_file)

        assert "VulDeePecker" in result
        assert "BigVul" in result


class TestValidateUrlPattern:
    """Tests for validate_url_pattern function."""

    def test_matching_pattern(self):
        """Test URL matching against valid pattern."""
        url = "https://github.com/example/vuldeepecker"
        patterns = [r"https://github\.com/.*vuldeepecker.*"]

        assert validate_url_pattern(url, patterns) is True

    def test_non_matching_pattern(self):
        """Test URL not matching pattern."""
        url = "https://example.com/other"
        patterns = [r"https://github\.com/.*vuldeepecker.*"]

        assert validate_url_pattern(url, patterns) is False

    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        url = "HTTPS://GITHUB.COM/EXAMPLE/VULDEEPCKER"
        patterns = [r"https://github\.com/.*vuldeepecker.*"]

        assert validate_url_pattern(url, patterns) is True


class TestValidateDatasetUrls:
    """Tests for validate_dataset_urls function."""

    def test_all_valid_urls(self):
        """Test validation with all valid URLs."""
        dataset_urls = {
            "VulDeePecker": ["https://github.com/example/vuldeepecker"],
            "BigVul": ["https://github.com/example/bigvul"]
        }

        with patch('src.utils.validate_urls.check_url_accessibility') as mock_check:
            mock_check.return_value = (True, "Accessible (HTTP 200)")

            report = validate_dataset_urls(dataset_urls)

            assert report["valid"] is True
            assert len(report["missing_required"]) == 0

    def test_missing_required_dataset(self):
        """Test validation with missing required dataset."""
        dataset_urls = {
            "BigVul": ["https://github.com/example/bigvul"]
            # VulDeePecker is missing
        }

        report = validate_dataset_urls(dataset_urls)

        assert report["valid"] is False
        assert "VulDeePecker" in report["missing_required"]

    def test_inaccessible_url(self):
        """Test validation with inaccessible URL."""
        dataset_urls = {
            "VulDeePecker": ["https://invalid-url.example.com"]
        }

        with patch('src.utils.validate_urls.check_url_accessibility') as mock_check:
            mock_check.return_value = (False, "URL Error: Connection refused")

            report = validate_dataset_urls(dataset_urls)

            assert report["valid"] is False
            assert len(report["errors"]) > 0


class TestValidateUrls:
    """Tests for main validate_urls function."""

    def test_validate_success(self, tmp_path):
        """Test successful validation."""
        manifest_content = """
        # Research Manifest

        ### VulDeePecker
        - https://github.com/example/vuldeepecker

        ### BigVul
        - https://github.com/example/bigvul
        """
        manifest_file = tmp_path / "research.md"
        manifest_file.write_text(manifest_content)

        with patch('src.utils.validate_urls.check_url_accessibility') as mock_check:
            mock_check.return_value = (True, "Accessible (HTTP 200)")

            with patch('src.utils.validate_urls.RESEARCH_MD_PATH', manifest_file):
                result = validate_urls(manifest_file)

                assert result is True

    def test_validate_failure(self, tmp_path):
        """Test failed validation due to missing dataset."""
        manifest_content = """
        # Research Manifest

        ### BigVul
        - https://github.com/example/bigvul
        """
        manifest_file = tmp_path / "research.md"
        manifest_file.write_text(manifest_content)

        with patch('src.utils.validate_urls.RESEARCH_MD_PATH', manifest_file):
            result = validate_urls(manifest_file)

            assert result is False

    def test_manifest_not_found(self):
        """Test handling of missing manifest."""
        with patch('src.utils.validate_urls.RESEARCH_MD_PATH', Path("/non/existent/path.md")):
            result = validate_urls()
            assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])