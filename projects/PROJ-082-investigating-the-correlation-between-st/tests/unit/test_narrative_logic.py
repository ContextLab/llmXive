"""
Unit tests for narrative_logic.py (T015a)
"""
import json
import csv
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from code.analysis.narrative_logic import (
    load_methodology_config,
    load_extracted_studies,
    extract_themes,
    generate_themes_json,
    run_narrative_logic
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_methodology(temp_dir):
    """Create a sample methodology config."""
    config = {
        'keywords': ['arcuate fasciculus', 'auditory', 'reward', 'frontal'],
        'sentiment_rules': {
            'positive': ['increased', 'enhanced', 'stronger'],
            'negative': ['decreased', 'reduced', 'weaker']
        },
        'exclusion_criteria': ['insufficient data', 'no correlation']
    }
    config_path = temp_dir / 'narrative_methodology.yaml'
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    return config_path

@pytest.fixture
def sample_studies_csv(temp_dir):
    """Create a sample extracted studies CSV."""
    csv_path = temp_dir / 'extracted_studies.csv'
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['author', 'year', 'tract', 'r', 'n', 'qualitative_desc', 'narrative_pool'])
        writer.writeheader()
        writer.writerows([
            {'author': 'Smith et al.', 'year': '2020', 'tract': 'arcuate fasciculus', 'r': '', 'n': '', 'qualitative_desc': 'Increased connectivity in arcuate fasciculus associated with musical training', 'narrative_pool': 'true'},
            {'author': 'Jones et al.', 'year': '2019', 'tract': 'auditory cortex', 'r': '', 'n': '', 'qualitative_desc': 'Enhanced auditory cortex activation during music perception', 'narrative_pool': 'true'},
            {'author': 'Lee et al.', 'year': '2021', 'tract': 'frontal', 'r': '', 'n': '', 'qualitative_desc': 'Weaker frontal connectivity in non-musicians', 'narrative_pool': 'true'},
            {'author': 'NoDesc et al.', 'year': '2022', 'tract': 'unknown', 'r': '', 'n': '', 'qualitative_desc': 'no_descriptor_found', 'narrative_pool': 'true'},
        ])
    return csv_path

def test_load_methodology_config(sample_methodology):
    """Test loading methodology config."""
    config = load_methodology_config(sample_methodology)
    assert 'keywords' in config
    assert 'sentiment_rules' in config
    assert len(config['keywords']) > 0

def test_load_methodology_config_missing():
    """Test loading missing methodology config raises error."""
    with pytest.raises(FileNotFoundError):
        load_methodology_config(Path('/nonexistent/path.yaml'))

def test_load_extracted_studies(sample_studies_csv):
    """Test loading extracted studies."""
    studies = load_extracted_studies(sample_studies_csv)
    assert len(studies) == 4
    assert studies[0]['author'] == 'Smith et al.'

def test_load_extracted_studies_missing():
    """Test loading missing studies CSV raises error."""
    with pytest.raises(FileNotFoundError):
        load_extracted_studies(Path('/nonexistent/path.csv'))

def test_extract_themes(sample_methodology, sample_studies_csv):
    """Test theme extraction logic."""
    methodology = load_methodology_config(sample_methodology)
    studies = load_extracted_studies(sample_studies_csv)
    
    themes = extract_themes(studies, methodology)
    
    # Check that themes were extracted
    assert 'arcuate fasciculus' in themes
    assert 'auditory' in themes
    assert 'frontal' in themes
    assert 'positive_sentiment' in themes
    assert 'negative_sentiment' in themes

def test_extract_themes_empty_desc(sample_methodology, temp_dir):
    """Test extraction with empty descriptors."""
    csv_path = temp_dir / 'empty.csv'
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['qualitative_desc'])
        writer.writeheader()
        writer.writerow({'qualitative_desc': 'no_descriptor_found'})
        writer.writerow({'qualitative_desc': ''})
    
    methodology = load_methodology_config(sample_methodology)
    studies = load_extracted_studies(csv_path)
    themes = extract_themes(studies, methodology)
    
    # Should not count empty or no_descriptor_found
    assert len(themes) == 0

def test_generate_themes_json(sample_methodology, sample_studies_csv, temp_dir):
    """Test JSON output generation."""
    methodology = load_methodology_config(sample_methodology)
    studies = load_extracted_studies(sample_studies_csv)
    themes = extract_themes(studies, methodology)
    
    output_path = temp_dir / 'narrative_themes.json'
    result_path = generate_themes_json(themes, output_path)
    
    assert result_path.exists()
    
    with open(result_path, 'r') as f:
        data = json.load(f)
    
    assert 'timestamp' in data
    assert 'theme_counts' in data
    assert 'total_themes_identified' in data

def test_run_narrative_logic_full_flow(sample_methodology, sample_studies_csv, temp_dir):
    """Test the full narrative logic flow."""
    output_path = temp_dir / 'narrative_themes.json'
    
    result = run_narrative_logic(
        csv_path=sample_studies_csv,
        config_path=sample_methodology,
        output_path=output_path
    )
    
    assert result['status'] == 'completed'
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert 'theme_counts' in data
    assert data['total_themes_identified'] > 0

def test_run_narrative_logic_missing_csv(sample_methodology, temp_dir):
    """Test error handling for missing CSV."""
    with pytest.raises(FileNotFoundError):
        run_narrative_logic(
            csv_path=Path('/nonexistent.csv'),
            config_path=sample_methodology,
            output_path=temp_dir / 'out.json'
        )

def test_run_narrative_logic_missing_config(sample_studies_csv, temp_dir):
    """Test error handling for missing config."""
    with pytest.raises(FileNotFoundError):
        run_narrative_logic(
            csv_path=sample_studies_csv,
            config_path=Path('/nonexistent.yaml'),
            output_path=temp_dir / 'out.json'
        )