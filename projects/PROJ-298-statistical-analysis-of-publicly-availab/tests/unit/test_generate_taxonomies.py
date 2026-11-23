import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.generate_taxonomies import (
    fetch_survey_2023_taxonomy,
    generate_reference_calendar,
    validate_taxonomy_structure,
    ensure_output_dir
)

class TestValidateTaxonomyStructure:
    def test_valid_structure(self):
        valid_taxonomy = {
            "tags": ["python", "java"],
            "categories": {"Tech Stack": ["python", "java"]}
        }
        assert validate_taxonomy_structure(valid_taxonomy) is True

    def test_missing_tags(self):
        invalid_taxonomy = {
            "categories": {"Tech Stack": ["python"]}
        }
        assert validate_taxonomy_structure(invalid_taxonomy) is False

    def test_missing_categories(self):
        invalid_taxonomy = {
            "tags": ["python", "java"]
        }
        assert validate_taxonomy_structure(invalid_taxonomy) is False

    def test_invalid_tags_type(self):
        invalid_taxonomy = {
            "tags": "python",
            "categories": {"Tech Stack": ["python"]}
        }
        assert validate_taxonomy_structure(invalid_taxonomy) is False

class TestFetchSurvey2023Taxonomy:
    @patch('data.generate_taxonomies.load_dataset')
    def test_fetch_success(self, mock_load_dataset):
        # Mock the dataset
        mock_ds = MagicMock()
        mock_ds.__iter__ = MagicMock(return_value=iter([
            {"TechStack": ["Python", "JavaScript"]},
            {"TechStack": ["Java", "C#"]},
            {"TechStack": ["Python", "Go"]}
        ]))
        mock_load_dataset.return_value = mock_ds

        result = fetch_survey_2023_taxonomy()

        assert "tags" in result
        assert "categories" in result
        assert "Python" in result["tags"]
        assert "JavaScript" in result["tags"]
        assert "Java" in result["tags"]
        assert "C#" in result["tags"]
        assert "Go" in result["tags"]
        assert len(result["tags"]) == 5

    @patch('data.generate_taxonomies.load_dataset')
    def test_fetch_with_json_string(self, mock_load_dataset):
        # Mock the dataset with JSON string
        mock_ds = MagicMock()
        mock_ds.__iter__ = MagicMock(return_value=iter([
            {"TechStack": '["Python", "JavaScript"]'},
            {"TechStack": '["Java", "C#"]'}
        ]))
        mock_load_dataset.return_value = mock_ds

        result = fetch_survey_2023_taxonomy()

        assert "Python" in result["tags"]
        assert "JavaScript" in result["tags"]

    @patch('data.generate_taxonomies.load_dataset')
    def test_fetch_with_comma_separated(self, mock_load_dataset):
        # Mock the dataset with comma-separated string
        mock_ds = MagicMock()
        mock_ds.__iter__ = MagicMock(return_value=iter([
            {"TechStack": "Python, JavaScript"},
            {"TechStack": "Java, C#"}
        ]))
        mock_load_dataset.return_value = mock_ds

        result = fetch_survey_2023_taxonomy()

        assert "Python" in result["tags"]
        assert "JavaScript" in result["tags"]

    @patch('data.generate_taxonomies.load_dataset')
    def test_fetch_no_tech_column(self, mock_load_dataset):
        # Mock the dataset with no tech column
        mock_ds = MagicMock()
        mock_ds.__iter__ = MagicMock(return_value=iter([
            {"Name": "Alice", "Age": 30}
        ]))
        mock_load_dataset.return_value = mock_ds

        with pytest.raises(ValueError, match="Could not identify a 'Tech Stack' related column"):
            fetch_survey_2023_taxonomy()

class TestGenerateReferenceCalendar:
    @patch('data.generate_taxonomies.requests.get')
    def test_fetch_rss_success(self, mock_get):
        # Mock RSS response
        mock_response = MagicMock()
        mock_response.content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
          <channel>
            <item>
              <title>Stack Overflow Blog Post 1</title>
              <pubDate>Mon, 01 Jan 2023 12:00:00 GMT</pubDate>
              <link>https://stackoverflow.blog/1</link>
            </item>
            <item>
              <title>Stack Overflow Blog Post 2</title>
              <pubDate>Tue, 02 Jan 2023 12:00:00 GMT</pubDate>
              <link>https://stackoverflow.blog/2</link>
            </item>
          </channel>
        </rss>"""
        mock_get.return_value = mock_response

        result = generate_reference_calendar()

        assert "events" in result
        assert len(result["events"]) == 2
        assert result["events"][0]["title"] == "Stack Overflow Blog Post 1"
        assert result["events"][0]["date"] == "Mon, 01 Jan 2023 12:00:00 GMT"
        assert result["events"][0]["type"] == "blog_post"

    @patch('data.generate_taxonomies.requests.get')
    def test_fetch_rss_failure(self, mock_get):
        mock_get.side_effect = Exception("Network error")

        with pytest.raises(ValueError, match="Could not fetch release logs"):
            generate_reference_calendar()

class TestEnsureOutputDir:
    def test_creates_directory(self, tmp_path):
        test_dir = tmp_path / "sub" / "dir"
        ensure_output_dir(test_dir)
        assert test_dir.exists()
        assert test_dir.is_dir()
