"""
Unit tests for T015a: Narrative Logic Module.
"""
import json
import csv
import tempfile
import os
from pathlib import Path
import pytest
from collections import defaultdict

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.narrative_logic import (
    load_methodology_config,
    load_extracted_studies,
    extract_themes,
    generate_themes_json
)

@pytest.fixture
def temp_methodology_config():
    """Create a temporary methodology config file."""
    content = """
    keywords:
      - "arcuate fasciculus"
      - "correlation"
      - "preference"
    
    sentiment_rules:
      positive:
        - "increased"
        - "stronger"
      negative:
        - "decreased"
        - "weaker"
    
    exclusion_criteria:
      - "no_descriptor_found"
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(content)
        return Path(f.name)

@pytest.fixture
def temp_extracted_studies_csv():
    """Create a temporary extracted studies CSV file."""
    content = """author,year,tract,r,n,qualitative_desc,narrative_pool
    Smith,2020,arcuate fasciculus,,,"Studies show arcuate fasciculus correlation with musical preference",true
    Jones,2021,cingulum,0.3,50,"Increased cingulum activity associated with rhythm preference",false
    Lee,2022,uncinate,,,"No clear association found between uncinate and preference",true
    Brown,2023,ventral striatum,0.5,100,"Weaker ventral striatum response in low-pitch preference",false
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(content)
        return Path(f.name)

def test_load_methodology_config(temp_methodology_config):
    """Test loading the methodology configuration."""
    config = load_methodology_config(temp_methodology_config)
    assert 'keywords' in config
    assert 'sentiment_rules' in config
    assert 'exclusion_criteria' in config
    assert len(config['keywords']) > 0

def test_load_extracted_studies(temp_extracted_studies_csv):
    """Test loading extracted studies from CSV."""
    studies = load_extracted_studies(temp_extracted_studies_csv)
    assert len(studies) == 4
    assert studies[0]['author'] == 'Smith'
    assert studies[1]['tract'] == 'cingulum'

def test_extract_themes(temp_methodology_config, temp_extracted_studies_csv):
    """Test theme extraction logic."""
    config = load_methodology_config(temp_methodology_config)
    studies = load_extracted_studies(temp_extracted_studies_csv)
    
    theme_counts = extract_themes(studies, config)
    
    # Check that expected themes are counted
    assert 'arcuate fasciculus' in theme_counts
    assert theme_counts['arcuate fasciculus'] >= 1
    assert 'correlation' in theme_counts
    assert 'increased_sentiment' in theme_counts
    assert 'decreased_sentiment' in theme_counts or 'weaker_sentiment' in theme_counts

def test_generate_themes_json(temp_methodology_config, temp_extracted_studies_csv):
    """Test generating the themes JSON output."""
    config = load_methodology_config(temp_methodology_config)
    studies = load_extracted_studies(temp_extracted_studies_csv)
    theme_counts = extract_themes(studies, config)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_themes.json"
        result_path = generate_themes_json(theme_counts, output_path)
        
        assert result_path.exists()
        with open(result_path, 'r') as f:
            data = json.load(f)
        
        assert 'timestamp' in data
        assert 'theme_counts' in data
        assert data['total_themes_identified'] == len(theme_counts)

def test_empty_qualitative_desc(temp_methodology_config, temp_extracted_studies_csv):
    """Test handling of empty qualitative descriptions."""
    config = load_methodology_config(temp_methodology_config)
    
    # Create a study with empty description
    studies = [{'qualitative_desc': ''}, {'qualitative_desc': 'no_descriptor_found'}]
    
    theme_counts = extract_themes(studies, config)
    
    # Should not count themes for empty descriptors
    assert sum(theme_counts.values()) == 0

def test_missing_config_file():
    """Test error handling for missing config file."""
    with pytest.raises(FileNotFoundError):
        load_methodology_config(Path("/nonexistent/path/config.yaml"))

def test_missing_csv_file():
    """Test error handling for missing CSV file."""
    with pytest.raises(FileNotFoundError):
        load_extracted_studies(Path("/nonexistent/path/studies.csv"))