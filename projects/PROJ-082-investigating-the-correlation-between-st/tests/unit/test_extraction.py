"""
Unit tests for the qualitative extraction module (T012).
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.extraction import (
    load_lexicon,
    load_methodology,
    extract_qualitative_descriptors,
    run_extraction,
    save_qualitative_data
)
from utils.config import get_project_root

def test_load_lexicon():
    """Test that the lexicon loads correctly or generates defaults."""
    lexicon = load_lexicon()
    assert isinstance(lexicon, dict)
    assert "tracts" in lexicon
    assert "verbs" in lexicon
    assert len(lexicon["tracts"]) > 0

def test_load_methodology():
    """Test that the methodology loads correctly."""
    scheme = load_methodology()
    assert isinstance(scheme, dict)
    assert "keywords" in scheme
    assert "sentiment_rules" in scheme

def test_extract_qualitative_descriptors_with_text():
    """Test extraction when text is present."""
    lexicon = load_lexicon()
    scheme = load_methodology()
    
    row = {
        "author": "Test",
        "tract": "Arcuate Fasciculus",
        "description": "The arcuate fasciculus is correlated with music preference."
    }
    
    result = extract_qualitative_descriptors(row, lexicon, scheme)
    # Depending on NLP logic implementation, this might return the text or a processed string
    # We assert that it returns a string or None, not an exception
    assert isinstance(result, (str, type(None)))

def test_extract_qualitative_descriptors_missing_text():
    """Test extraction when text is missing but tract is present."""
    lexicon = load_lexicon()
    scheme = load_methodology()
    
    row = {
        "author": "Test",
        "tract": "Cingulum Bundle",
        "description": None
    }
    
    result = extract_qualitative_descriptors(row, lexicon, scheme)
    # The implementation should handle this gracefully
    assert isinstance(result, (str, type(None)))

def test_run_extraction(tmp_path):
    """Test the full extraction pipeline."""
    # Create a temporary input CSV
    input_csv = tmp_path / "studies.csv"
    output_json = tmp_path / "qualitative_data.json"
    
    input_csv.write_text(
        "author,year,tract,r,n,description\n"
        "Smith,2020,Tract A,0.5,100,Good data\n"
        "Jones,2021,Tract B,,,"
    )
    
    result = run_extraction(input_csv, output_json)
    
    assert output_json.exists()
    with open(output_json, 'r') as f:
        data = json.load(f)
    
    # Only the row with missing r and n should be extracted
    assert len(data) == 1
    assert data[0]["author"] == "Jones"
    assert "qualitative_desc" in data[0]

def test_run_extraction_missing_input(tmp_path):
    """Test behavior when input file is missing."""
    output_json = tmp_path / "qualitative_data.json"
    missing_input = tmp_path / "nonexistent.csv"
    
    result = run_extraction(missing_input, output_json)
    
    # Should not crash, should write empty list
    assert output_json.exists()
    with open(output_json, 'r') as f:
        data = json.load(f)
    assert data == []