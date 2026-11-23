"""
Unit tests for the extraction parser module.
"""
import pytest
import json
import csv
import os
from pathlib import Path
import tempfile
import sys

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from extraction.parser import (
    parse_row, 
    parse_csv_file, 
    parse_json_file, 
    save_extracted_studies, 
    load_qualitative_data,
    log_exclusion,
    load_tract_lexicon
)

@pytest.fixture
def sample_lexicon():
    return ["arcuate fasciculus", "cingulum bundle", "uncinate fasciculus"]

@pytest.fixture
def sample_qualitative_data():
    return {
        "Smith_2020": "Strong correlation with auditory cortex",
        "Jones_2021": "No significant findings reported"
    }

def test_parse_row_valid_quantitative(sample_lexicon):
    """Test parsing a row with valid r and n values."""
    row = {
        "author": "Smith",
        "year": 2020,
        "tract": "Arcuate Fasciculus",
        "r": 0.45,
        "n": 50
    }
    qualitative_data = {}
    
    result, reason = parse_row(row, sample_lexicon, qualitative_data)
    
    assert result is not None
    assert reason is None
    assert result['author'] == "Smith"
    assert result['year'] == 2020
    assert result['tract'] == "arcuate fasciculus"
    assert result['r'] == 0.45
    assert result['n'] == 50
    assert result['narrative_pool'] == False

def test_parse_row_missing_r_with_qualitative(sample_lexicon, sample_qualitative_data):
    """Test parsing a row missing r but with qualitative data."""
    row = {
        "author": "Smith",
        "year": 2020,
        "tract": "Arcuate Fasciculus",
        "r": "",
        "n": 50
    }
    
    result, reason = parse_row(row, sample_lexicon, sample_qualitative_data)
    
    assert result is not None
    assert reason is None
    assert result['qualitative_desc'] == "Strong correlation with auditory cortex"
    assert result['narrative_pool'] == True

def test_parse_row_missing_both_and_no_qualitative(sample_lexicon):
    """Test parsing a row missing both r and n with no qualitative data."""
    row = {
        "author": "Unknown",
        "year": 2023,
        "tract": "Cingulum Bundle",
        "r": "",
        "n": ""
    }
    qualitative_data = {}
    
    result, reason = parse_row(row, sample_lexicon, qualitative_data)
    
    assert result is None
    assert reason == "Missing r, n, and qualitative description"

def test_parse_row_missing_author(sample_lexicon):
    """Test parsing a row missing author."""
    row = {
        "author": "",
        "year": 2020,
        "tract": "Cingulum Bundle",
        "r": 0.3,
        "n": 40
    }
    
    result, reason = parse_row(row, sample_lexicon, {})
    
    assert result is None
    assert reason == "Missing author or year"

def test_parse_csv_file(tmp_path, sample_lexicon, sample_qualitative_data):
    """Test parsing a CSV file."""
    csv_file = tmp_path / "studies.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['author', 'year', 'tract', 'r', 'n'])
        writer.writeheader()
        writer.writerow({"author": "Smith", "year": 2020, "tract": "Arcuate Fasciculus", "r": 0.45, "n": 50})
        writer.writerow({"author": "Jones", "year": 2021, "tract": "Cingulum Bundle", "r": "", "n": 30})
    
    studies, exclusions = parse_csv_file(csv_file, sample_qualitative_data)
    
    assert len(studies) == 2
    assert len(exclusions) == 0
    assert studies[0]['author'] == "Smith"
    assert studies[1]['qualitative_desc'] == "No significant findings reported"

def test_save_extracted_studies(tmp_path):
    """Test saving extracted studies to CSV."""
    studies = [
        {"author": "Smith", "year": 2020, "tract": "Arcuate Fasciculus", "r": 0.45, "n": 50, "qualitative_desc": None, "narrative_pool": False},
        {"author": "Jones", "year": 2021, "tract": "Cingulum Bundle", "r": None, "n": 30, "qualitative_desc": "Test desc", "narrative_pool": True}
    ]
    output_path = tmp_path / "extracted.csv"
    
    save_extracted_studies(studies, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 2
    assert rows[0]['r'] == '0.45'
    assert rows[1]['r'] == ''
    assert rows[1]['narrative_pool'] == 'True'

def test_log_exclusion(tmp_path):
    """Test logging an excluded row."""
    exclusion_log_path = tmp_path / "exclusions.csv"
    row = {"author": "Test", "year": 2022, "tract": "Unknown", "r": "", "n": ""}
    
    log_exclusion(row, "Missing data", exclusion_log_path)
    
    assert exclusion_log_path.exists()
    with open(exclusion_log_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 1
    assert rows[0]['reason'] == "Missing data"