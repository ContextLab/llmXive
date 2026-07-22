import csv
import json
import tempfile
import os
from pathlib import Path
import pytest
import yaml

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from extraction.parser import parse_row, parse_csv_file, parse_json_file, save_extracted_studies, load_tract_lexicon
from utils.config import get_project_root

@pytest.fixture
def mock_lexicon():
    """Create a temporary mock lexicon for testing."""
    return {
        "directional_verbs": ["increased", "decreased", "correlated", "associated"],
        "tracts": ["arcuate fasciculus", "cingulum bundle", "uncinate fasciculus"]
    }

@pytest.fixture
def exclusion_log_path(tmp_path):
    return tmp_path / "exclusion_log.csv"

def test_parse_row_with_r_n(mock_lexicon, exclusion_log_path):
    """Test parsing a row with r and n values."""
    row = {
        "author": "Smith",
        "year": 2020,
        "tract": "arcuate fasciculus",
        "r": 0.5,
        "n": 100,
        "qualitative_desc": "The arcuate fasciculus showed increased connectivity."
    }
    
    result = parse_row(row, mock_lexicon, exclusion_log_path)
    
    assert result["author"] == "Smith"
    assert result["year"] == 2020
    assert result["tract"] == "arcuate fasciculus"
    assert result["r"] == 0.5
    assert result["n"] == 100
    assert result["narrative_pool"] == True  # Because descriptors were found
    assert "increased" in result["qualitative_desc"]

def test_parse_row_without_descriptors(mock_lexicon, exclusion_log_path):
    """Test parsing a row with r and n but no qualitative descriptors."""
    row = {
        "author": "Jones",
        "year": 2021,
        "tract": "cingulum bundle",
        "r": 0.3,
        "n": 50,
        "qualitative_desc": "Some random text without tract terms."
    }
    
    result = parse_row(row, mock_lexicon, exclusion_log_path)
    
    assert result["narrative_pool"] == False
    assert result["qualitative_desc"] == ""
    
    # Check exclusion log
    assert exclusion_log_path.exists()
    with open(exclusion_log_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["reason"] == "No tract-directional verb pair found in text"

def test_parse_row_with_p_value(mock_lexicon, exclusion_log_path):
    """Test parsing a row with p-value and n, but no r."""
    # Assuming p=0.05, n=100 converts to a small r
    row = {
        "author": "Doe",
        "year": 2022,
        "tract": "uncinate fasciculus",
        "p": 0.05,
        "n": 100,
        "qualitative_desc": "uncinate fasciculus associated with reward."
    }
    
    result = parse_row(row, mock_lexicon, exclusion_log_path)
    
    assert result["r"] is not None  # Should be converted
    assert result["n"] == 100
    assert result["narrative_pool"] == True  # Because "associated" was found

def test_parse_csv_file(tmp_path, mock_lexicon):
    """Test parsing a CSV file."""
    csv_path = tmp_path / "input.csv"
    exclusion_log_path = tmp_path / "exclusion_log.csv"
    
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["author", "year", "tract", "r", "n", "qualitative_desc"])
        writer.writeheader()
        writer.writerow({
            "author": "Test1",
            "year": 2020,
            "tract": "arcuate fasciculus",
            "r": 0.4,
            "n": 80,
            "qualitative_desc": "arcuate fasciculus increased connectivity."
        })
        writer.writerow({
            "author": "Test2",
            "year": 2021,
            "tract": "cingulum bundle",
            "r": 0.2,
            "n": 60,
            "qualitative_desc": "random text."
        })
    
    studies = parse_csv_file(csv_path, mock_lexicon, exclusion_log_path)
    
    assert len(studies) == 2
    assert studies[0]["narrative_pool"] == True
    assert studies[1]["narrative_pool"] == False

def test_parse_json_file(tmp_path, mock_lexicon):
    """Test parsing a JSON file."""
    json_path = tmp_path / "input.json"
    exclusion_log_path = tmp_path / "exclusion_log.csv"
    
    data = [
        {
            "author": "Test1",
            "year": 2020,
            "tract": "arcuate fasciculus",
            "r": 0.4,
            "n": 80,
            "qualitative_desc": "arcuate fasciculus increased connectivity."
        },
        {
            "author": "Test2",
            "year": 2021,
            "tract": "cingulum bundle",
            "r": 0.2,
            "n": 60,
            "qualitative_desc": "random text."
        }
    ]
    
    with open(json_path, 'w') as f:
        json.dump(data, f)
    
    studies = parse_json_file(json_path, mock_lexicon, exclusion_log_path)
    
    assert len(studies) == 2
    assert studies[0]["narrative_pool"] == True
    assert studies[1]["narrative_pool"] == False

def test_save_extracted_studies(tmp_path, mock_lexicon):
    """Test saving extracted studies to CSV."""
    studies = [
        {"author": "A", "year": 2020, "tract": "T1", "r": 0.1, "n": 10, "qualitative_desc": "desc1", "narrative_pool": True},
        {"author": "B", "year": 2021, "tract": "T2", "r": 0.2, "n": 20, "qualitative_desc": "", "narrative_pool": False}
    ]
    
    output_path = tmp_path / "output.csv"
    save_extracted_studies(studies, output_path)
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["author"] == "A"
        assert rows[0]["narrative_pool"] == "True"
        assert rows[1]["author"] == "B"
        assert rows[1]["narrative_pool"] == "False"
