import os
import json
from pathlib import Path
import pytest
from data.setup_data_structure import create_directories, fetch_survey_2023_taxonomy, generate_reference_calendar

@pytest.fixture
def temp_data_path(tmp_path):
    """Create a temporary directory for testing."""
    return tmp_path / "data"

def test_create_directories(temp_data_path):
    """Test that create_directories creates the expected subdirectories."""
    create_directories(temp_data_path)
    
    expected_dirs = ["raw", "processed", "events", "taxonomy"]
    for dir_name in expected_dirs:
        assert (temp_data_path / dir_name).exists()
        assert (temp_data_path / dir_name).is_dir()

def test_fetch_survey_2023_taxonomy(temp_data_path):
    """Test that fetch_survey_2023_taxonomy creates a valid JSON file."""
    taxonomy_path = temp_data_path / "taxonomy"
    taxonomy_path.mkdir(parents=True, exist_ok=True)
    
    fetch_survey_2023_taxonomy(taxonomy_path)
    
    output_file = taxonomy_path / "survey_2023.json"
    assert output_file.exists()
    
    with open(output_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert "year" in data
    assert data["year"] == 2023
    assert "categories" in data
    assert "metadata" in data

def test_generate_reference_calendar(temp_data_path):
    """Test that generate_reference_calendar creates a valid JSON file."""
    events_path = temp_data_path / "events"
    events_path.mkdir(parents=True, exist_ok=True)
    
    generate_reference_calendar(events_path)
    
    output_file = events_path / "reference_calendar.json"
    assert output_file.exists()
    
    with open(output_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert "events" in data
    assert "metadata" in data
    assert len(data["events"]) > 0