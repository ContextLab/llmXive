import pytest
import csv
import json
import tempfile
from pathlib import Path
import yaml

from extraction.parser import (
    parse_row,
    parse_csv_file,
    parse_json_file,
    log_exclusion,
    load_tract_lexicon,
    save_extracted_studies
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_lexicon():
    return {
        'tracts': ['arcuate fasciculus', 'cingulum bundle'],
        'verbs': ['increased', 'decreased', 'correlated']
    }

@pytest.fixture
def mock_scheme():
    return {
        'keywords': ['music', 'auditory'],
        'sentiment_rules': {
            'positive': ['strong', 'significant'],
            'negative': ['weak', 'no']
        },
        'exclusion_criteria': ['review', 'meta-analysis']
    }

@pytest.fixture
def exclusion_log_path(temp_dir):
    log_path = temp_dir / "exclusion_log.csv"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    return log_path

def test_parse_row_valid_quantitative(mock_lexicon, mock_scheme, exclusion_log_path):
    """Test parsing a row with valid r and n values."""
    row = {
        'author': 'Smith',
        'year': 2020,
        'tract': 'arcuate fasciculus',
        'r': 0.45,
        'n': 50
    }
    
    parsed, is_valid = parse_row(row, 'study_001', mock_lexicon, mock_scheme, exclusion_log_path)
    
    assert parsed['author'] == 'Smith'
    assert parsed['r'] == 0.45
    assert parsed['n'] == 50
    assert parsed['narrative_pool'] == False
    assert is_valid == True

def test_parse_row_missing_r(mock_lexicon, mock_scheme, exclusion_log_path):
    """Test parsing a row with missing r value."""
    row = {
        'author': 'Johnson',
        'year': 2019,
        'tract': 'cingulum bundle',
        'r': None,
        'n': 30
    }
    
    parsed, is_valid = parse_row(row, 'study_002', mock_lexicon, mock_scheme, exclusion_log_path)
    
    assert parsed['r'] is None
    assert parsed['n'] == 30
    assert parsed['narrative_pool'] == True
    assert parsed['exclusion_reason'] == 'r_missing'
    assert is_valid == False

def test_parse_row_missing_n(mock_lexicon, mock_scheme, exclusion_log_path):
    """Test parsing a row with missing n value."""
    row = {
        'author': 'Williams',
        'year': 2021,
        'tract': 'uncinate fasciculus',
        'r': 0.32,
        'n': None
    }
    
    parsed, is_valid = parse_row(row, 'study_003', mock_lexicon, mock_scheme, exclusion_log_path)
    
    assert parsed['r'] == 0.32
    assert parsed['n'] is None
    assert parsed['narrative_pool'] == True
    assert parsed['exclusion_reason'] == 'n_missing'
    assert is_valid == False

def test_parse_row_invalid_r_format(mock_lexicon, mock_scheme, exclusion_log_path):
    """Test parsing a row with invalid r format."""
    row = {
        'author': 'Brown',
        'year': 2018,
        'tract': 'inferior longitudinal fasciculus',
        'r': 'invalid',
        'n': 40
    }
    
    parsed, is_valid = parse_row(row, 'study_004', mock_lexicon, mock_scheme, exclusion_log_path)
    
    assert parsed['r'] is None
    assert parsed['exclusion_reason'] == 'r_invalid_format'
    assert parsed['narrative_pool'] == True
    assert is_valid == False

def test_parse_row_r_out_of_range(mock_lexicon, mock_scheme, exclusion_log_path):
    """Test parsing a row with r out of valid range."""
    row = {
        'author': 'Davis',
        'year': 2022,
        'tract': 'auditory cortex',
        'r': 1.5,
        'n': 25
    }
    
    parsed, is_valid = parse_row(row, 'study_005', mock_lexicon, mock_scheme, exclusion_log_path)
    
    assert parsed['r'] is None
    assert parsed['exclusion_reason'] == 'r_out_of_range'
    assert parsed['narrative_pool'] == True
    assert is_valid == False

def test_parse_row_p_value_conversion(mock_lexicon, mock_scheme, exclusion_log_path):
    """Test parsing a row with p-value that gets converted."""
    row = {
        'author': 'Miller',
        'year': 2020,
        'tract': 'ventral striatum',
        'r': None,
        'n': 45,
        'p_value': 0.01
    }
    
    parsed, is_valid = parse_row(row, 'study_006', mock_lexicon, mock_scheme, exclusion_log_path)
    
    # Should have converted p-value to r
    assert parsed['r'] is not None
    assert parsed['n'] == 45
    assert parsed['exclusion_reason'] == 'converted_from_p_value'
    assert is_valid == True

def test_log_exclusion_creates_file(exclusion_log_path):
    """Test that log_exclusion creates the file with correct headers."""
    log_exclusion(exclusion_log_path, 'test_study', 'test_reason', 'test_value')
    
    assert exclusion_log_path.exists()
    
    with open(exclusion_log_path, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)
        assert headers == ['study_id', 'reason', 'original_value']
        
        row = next(reader)
        assert row == ['test_study', 'test_reason', 'test_value']

def test_log_exclusion_appends(exclusion_log_path):
    """Test that log_exclusion appends to existing file."""
    log_exclusion(exclusion_log_path, 'study1', 'reason1', 'value1')
    log_exclusion(exclusion_log_path, 'study2', 'reason2', 'value2')
    
    with open(exclusion_log_path, 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert len(rows) == 3  # header + 2 data rows
        assert rows[1] == ['study1', 'reason1', 'value1']
        assert rows[2] == ['study2', 'reason2', 'value2']

def test_parse_csv_file(temp_dir, mock_lexicon, mock_scheme):
    """Test parsing a CSV file with mixed valid and invalid rows."""
    input_path = temp_dir / "input.csv"
    exclusion_log_path = temp_dir / "logs" / "exclusion_log.csv"
    output_path = temp_dir / "output.csv"
    
    # Create input CSV
    with open(input_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['author', 'year', 'tract', 'r', 'n'])
        writer.writerow(['Valid', '2020', 'tract1', '0.5', '100'])
        writer.writerow(['MissingR', '2019', 'tract2', '', '50'])
        writer.writerow(['MissingN', '2021', 'tract3', '0.3', ''])
    
    studies, quant_count, narr_count = parse_csv_file(
        input_path, mock_lexicon, mock_scheme, exclusion_log_path
    )
    
    assert len(studies) == 3
    assert quant_count == 1
    assert narr_count == 2
    
    # Verify exclusion log was created
    assert exclusion_log_path.exists()

def test_parse_json_file(temp_dir, mock_lexicon, mock_scheme):
    """Test parsing a JSON file."""
    input_path = temp_dir / "input.json"
    exclusion_log_path = temp_dir / "logs" / "exclusion_log.csv"
    
    # Create input JSON
    data = [
        {'author': 'Test1', 'year': 2020, 'tract': 't1', 'r': 0.4, 'n': 60},
        {'author': 'Test2', 'year': 2019, 'tract': 't2', 'r': None, 'n': 40}
    ]
    
    with open(input_path, 'w') as f:
        json.dump(data, f)
    
    studies, quant_count, narr_count = parse_json_file(
        input_path, mock_lexicon, mock_scheme, exclusion_log_path
    )
    
    assert len(studies) == 2
    assert quant_count == 1
    assert narr_count == 1

def test_save_extracted_studies(temp_dir):
    """Test saving extracted studies to CSV."""
    studies = [
        {
            'study_id': 's1',
            'author': 'A',
            'year': 2020,
            'tract': 't1',
            'r': 0.5,
            'n': 100,
            'qualitative_desc': 'desc1',
            'narrative_pool': False,
            'exclusion_reason': None
        },
        {
            'study_id': 's2',
            'author': 'B',
            'year': 2019,
            'tract': 't2',
            'r': None,
            'n': 50,
            'qualitative_desc': 'desc2',
            'narrative_pool': True,
            'exclusion_reason': 'r_missing'
        }
    ]
    
    output_path = temp_dir / "output.csv"
    save_extracted_studies(studies, output_path)
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]['study_id'] == 's1'
        assert rows[1]['narrative_pool'] == 'True'
        assert rows[1]['exclusion_reason'] == 'r_missing'