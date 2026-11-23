"""
Unit tests for the extraction parser module.
"""

import csv
import json
import tempfile
from pathlib import Path
import pytest

# Import the module under test
from extraction.parser import (
    parse_row,
    parse_csv_file,
    parse_json_file,
    load_qualitative_data,
    save_extracted_studies,
    parse_input,
    load_tract_lexicon
)

@pytest.fixture
def tract_lexicon():
    """Provide a default tract lexicon for testing."""
    return [
        "arcuate fasciculus",
        "cingulum bundle",
        "uncinate fasciculus",
        "inferior longitudinal fasciculus",
        "auditory cortex",
        "ventral striatum"
    ]

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_parse_row_valid_quantitative(tract_lexicon):
    """Test parsing a row with valid quantitative data."""
    row = {
        'author': 'Smith',
        'year': '2020',
        'tract': 'Arcuate Fasciculus',
        'r': '0.45',
        'n': '100'
    }
    
    parsed, reason = parse_row(row, tract_lexicon)
    
    assert reason is None
    assert parsed['author'] == 'Smith'
    assert parsed['year'] == 2020
    assert parsed['tract'] == 'arcuate fasciculus'
    assert parsed['r'] == 0.45
    assert parsed['n'] == 100
    assert parsed['qualitative_desc'] is None
    assert parsed['narrative_pool'] is False

def test_parse_row_valid_qualitative_only(tract_lexicon):
    """Test parsing a row with only qualitative data."""
    row = {
        'author': 'Jones',
        'year': '2019',
        'tract': 'Cingulum Bundle',
        'qualitative_desc': 'Positive correlation observed'
    }
    
    parsed, reason = parse_row(row, tract_lexicon)
    
    assert reason is None
    assert parsed['author'] == 'Jones'
    assert parsed['qualitative_desc'] == 'Positive correlation observed'
    assert parsed['narrative_pool'] is True
    assert parsed['r'] is None
    assert parsed['n'] is None

def test_parse_row_missing_author(tract_lexicon):
    """Test that a row with missing author is excluded."""
    row = {
        'year': '2020',
        'tract': 'Arcuate Fasciculus',
        'r': '0.45'
    }
    
    parsed, reason = parse_row(row, tract_lexicon)
    
    assert parsed is None
    assert 'Missing author' in reason

def test_parse_row_invalid_year(tract_lexicon):
    """Test that a row with invalid year format is excluded."""
    row = {
        'author': 'Smith',
        'year': 'not_a_number',
        'tract': 'Arcuate Fasciculus',
        'r': '0.45'
    }
    
    parsed, reason = parse_row(row, tract_lexicon)
    
    assert parsed is None
    assert 'Invalid year format' in reason

def test_parse_row_missing_all_data(tract_lexicon):
    """Test that a row with no data is excluded."""
    row = {
        'author': 'Smith',
        'year': '2020'
    }
    
    parsed, reason = parse_row(row, tract_lexicon)
    
    assert parsed is None
    assert 'No quantitative' in reason

def test_parse_csv_file(temp_dir, tract_lexicon):
    """Test parsing a CSV file."""
    # Create test CSV
    csv_path = temp_dir / "test_studies.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['author', 'year', 'tract', 'r', 'n'])
        writer.writeheader()
        writer.writerow({'author': 'Smith', 'year': '2020', 'tract': 'Arcuate Fasciculus', 'r': '0.45', 'n': '100'})
        writer.writerow({'author': 'Jones', 'year': '2019', 'tract': 'Cingulum Bundle', 'r': '0.30', 'n': '80'})
    
    exclusion_path = temp_dir / "exclusions.csv"
    studies = parse_csv_file(csv_path, tract_lexicon, exclusion_path)
    
    assert len(studies) == 2
    assert studies[0]['author'] == 'Smith'
    assert studies[1]['author'] == 'Jones'

def test_parse_json_file(temp_dir, tract_lexicon):
    """Test parsing a JSON file."""
    # Create test JSON
    json_path = temp_dir / "test_studies.json"
    data = [
        {'author': 'Smith', 'year': '2020', 'tract': 'Arcuate Fasciculus', 'r': '0.45', 'n': '100'},
        {'author': 'Jones', 'year': '2019', 'tract': 'Cingulum Bundle', 'r': '0.30', 'n': '80'}
    ]
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    
    exclusion_path = temp_dir / "exclusions.csv"
    studies = parse_json_file(json_path, tract_lexicon, exclusion_path)
    
    assert len(studies) == 2
    assert studies[0]['author'] == 'Smith'

def test_load_qualitative_data(temp_dir):
    """Test loading qualitative data from JSON."""
    # Create test qualitative data
    qualitative_path = temp_dir / "qualitative_data.json"
    data = [
        {'author': 'Smith', 'year': '2020', 'qualitative_desc': 'Strong positive correlation'},
        {'author': 'Jones', 'year': '2019', 'qualitative_desc': 'Weak negative correlation'}
    ]
    with open(qualitative_path, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    
    qualitative_map = load_qualitative_data(qualitative_path)
    
    assert ('Smith', '2020') in qualitative_map
    assert qualitative_map[('Smith', '2020')] == 'Strong positive correlation'
    assert ('Jones', '2019') in qualitative_map

def test_save_extracted_studies(temp_dir):
    """Test saving extracted studies to CSV."""
    studies = [
        {'author': 'Smith', 'year': 2020, 'tract': 'arcuate fasciculus', 'r': 0.45, 'n': 100, 'qualitative_desc': None, 'narrative_pool': False, 'conversion_method': ''},
        {'author': 'Jones', 'year': 2019, 'tract': 'cingulum bundle', 'r': None, 'n': None, 'qualitative_desc': 'Positive', 'narrative_pool': True, 'conversion_method': ''}
    ]
    
    output_path = temp_dir / "extracted_studies.csv"
    save_extracted_studies(studies, output_path)
    
    assert output_path.exists()
    
    with open(output_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 2
    assert rows[0]['author'] == 'Smith'
    assert rows[0]['r'] == '0.45'
    assert rows[1]['qualitative_desc'] == 'Positive'
    assert rows[1]['narrative_pool'] == 'True'

def test_parse_input_integration(temp_dir, tract_lexicon):
    """Test the full parse_input workflow."""
    # Create input CSV
    input_path = temp_dir / "input_studies.csv"
    with open(input_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['author', 'year', 'tract', 'r', 'n'])
        writer.writeheader()
        writer.writerow({'author': 'Smith', 'year': '2020', 'tract': 'Arcuate Fasciculus', 'r': '0.45', 'n': '100'})
    
    # Create qualitative data
    qualitative_path = temp_dir / "qualitative_data.json"
    with open(qualitative_path, 'w', encoding='utf-8') as f:
        json.dump([{'author': 'Smith', 'year': '2020', 'qualitative_desc': 'Test description'}], f)
    
    output_path = temp_dir / "output.csv"
    exclusion_path = temp_dir / "exclusions.csv"
    
    studies = parse_input(
        input_path=input_path,
        qualitative_path=qualitative_path,
        output_path=output_path,
        exclusion_log_path=exclusion_path,
        lexicon_path=None
    )
    
    assert len(studies) == 1
    assert output_path.exists()
    assert exclusion_path.exists()
