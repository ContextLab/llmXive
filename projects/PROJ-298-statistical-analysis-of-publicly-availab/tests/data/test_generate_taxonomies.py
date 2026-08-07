import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import sys

# Add the project root to the path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.data.generate_taxonomies import (
    fetch_survey_2023_taxonomy,
    generate_reference_calendar,
    validate_taxonomy_structure,
    main
)

class TestFetchSurvey2023Taxonomy:
    def test_fetch_survey_2023_taxonomy_success(self):
        """Test successful fetch and parsing of survey data."""
        # Mock CSV response
        mock_csv = """Question,Python,JavaScript,Java
                    "Have you used...",Yes,No,Yes
                    "Have you used...",Yes,Yes,No
                    "Have you used...",No,Yes,Yes"""
        
        with patch('code.data.generate_taxonomies.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = mock_csv
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            result = fetch_survey_2023_taxonomy()
            
            # Verify structure
            assert "source" in result
            assert "url" in result
            assert "technologies" in result
            assert "categories" in result
            assert "metadata" in result
            
            # Verify content
            assert result["source"] == "Stack Overflow Developer Survey 2023"
            assert "Python" in result["technologies"]
            assert "JavaScript" in result["technologies"]
            assert result["metadata"]["survey_year"] == 2023

    def test_fetch_survey_2023_taxonomy_failure(self):
        """Test failure when fetching survey data."""
        with patch('code.data.generate_taxonomies.requests.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            with pytest.raises(RuntimeError, match="Failed to fetch"):
                fetch_survey_2023_taxonomy()

class TestGenerateReferenceCalendar:
    def test_generate_reference_calendar_structure(self):
        """Test that the generated calendar has the correct structure."""
        result = generate_reference_calendar()
        
        assert "description" in result
        assert "generated_at" in result
        assert "events" in result
        assert "categories" in result
        
        # Verify events are sorted by date
        dates = [event["date"] for event in result["events"]]
        assert dates == sorted(dates)
        
        # Verify event types
        event_types = set(event["type"] for event in result["events"])
        assert event_types.issubset({"survey", "conference", "release"})

    def test_generate_reference_calendar_contains_survey_events(self):
        """Test that the calendar contains survey release events."""
        result = generate_reference_calendar()
        
        survey_events = [e for e in result["events"] if e["type"] == "survey"]
        assert len(survey_events) > 0
        
        # Check for 2023 survey
        survey_2023 = [e for e in survey_events if "2023" in e["event"]]
        assert len(survey_2023) > 0

class TestValidateTaxonomyStructure:
    def test_validate_valid_taxonomy(self):
        """Test validation of a valid taxonomy."""
        valid_taxonomy = {
            "source": "Test",
            "url": "http://test.com",
            "technologies": ["Python"],
            "categories": {"lang": ["Python"]},
            "metadata": {"year": 2023}
        }
        
        assert validate_taxonomy_structure(valid_taxonomy) is True

    def test_validate_invalid_taxonomy_missing_keys(self):
        """Test validation of an invalid taxonomy with missing keys."""
        invalid_taxonomy = {
            "source": "Test",
            "url": "http://test.com"
            # Missing technologies, categories, metadata
        }
        
        assert validate_taxonomy_structure(invalid_taxonomy) is False

class TestMainFunction:
    def test_main_creates_files(self):
        """Test that main function creates the expected files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Mock the project root
            with patch('code.data.generate_taxonomies.PROJECT_ROOT', tmpdir_path):
                with patch('code.data.generate_taxonomies.requests.get') as mock_get:
                    mock_csv = """Question,Python,JavaScript
                                "Have you used...",Yes,No
                                "Have you used...",Yes,Yes"""
                    
                    mock_response = MagicMock()
                    mock_response.text = mock_csv
                    mock_response.raise_for_status = MagicMock()
                    mock_get.return_value = mock_response
                    
                    # Run main
                    result = main()
                    
                    assert result is True
                    
                    # Verify files were created
                    taxonomy_path = tmpdir_path / "data" / "taxonomy" / "survey_latest.json"
                    calendar_path = tmpdir_path / "data" / "events" / "reference_calendar.json"
                    
                    assert taxonomy_path.exists()
                    assert calendar_path.exists()
                    
                    # Verify JSON is valid
                    with open(taxonomy_path, 'r') as f:
                        taxonomy_data = json.load(f)
                        assert "technologies" in taxonomy_data
                    
                    with open(calendar_path, 'r') as f:
                        calendar_data = json.load(f)
                        assert "events" in calendar_data