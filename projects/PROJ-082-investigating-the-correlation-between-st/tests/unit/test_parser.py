import csv
import json
import os
import tempfile
import pytest
from pathlib import Path
import yaml

# Mock the logger to avoid issues in tests
import sys
from unittest.mock import MagicMock
sys.modules['utils.logger'] = MagicMock()
sys.modules['extraction.nlp_logic'] = MagicMock()
sys.modules['extraction.p_value_converter'] = MagicMock()

from extraction.parser import parse_row, parse_csv_file, save_extracted_studies, load_tract_lexicon, log_exclusion

@pytest.fixture
def sample_lexicon():
    return {
        "tracts": ["arcuate fasciculus"],
        "directional_verbs": ["increased", "correlated"],
        "themes": ["auditory"]
    }

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_parse_row_direct_values(sample_lexicon):
    row = {
        'author': 'Smith',
        'year': 2020,
        'tract': 'arcuate fasciculus',
        'r': 0.5,
        'n': 50,
        'notes': 'Some notes'
    }
    result = parse_row(row, sample_lexicon, None)
    assert result['author'] == 'Smith'
    assert result['r'] == 0.5
    assert result['n'] == 50
    assert result['narrative_pool'] is False

def test_parse_row_missing_r_n(sample_lexicon):
    # Mock nlp_logic to return a descriptor
    import extraction.nlp_logic
    extraction.nlp_logic.extract_tract_descriptors = MagicMock(return_value=["directional_verbs: increased"])
    
    row = {
        'author': 'Doe',
        'year': 2021,
        'tract': 'arcuate fasciculus',
        'r': None,
        'n': None,
        'notes': 'arcuate fasciculus was increased'
    }
    result = parse_row(row, sample_lexicon, None)
    assert result['r'] is None
    assert result['n'] is None
    assert result['qualitative_desc'] == "directional_verbs: increased"
    assert result['narrative_pool'] is True

def test_parse_row_no_data_excluded(sample_lexicon, temp_dir):
    # Mock nlp_logic to return empty
    import extraction.nlp_logic
    extraction.nlp_logic.extract_tract_descriptors = MagicMock(return_value=[])
    
    row = {
        'author': 'Empty',
        'year': 2022,
        'tract': 'unknown',
        'r': None,
        'n': None,
        'notes': 'no relevant info'
    }
    log_path = os.path.join(temp_dir, 'exclusion_log.csv')
    
    # We need to patch log_exclusion to not fail on file writing if not mocked, 
    # but here we just test the logic path.
    # The function log_exclusion is called inside parse_row if conditions met.
    
    result = parse_row(row, sample_lexicon, None)
    assert result['narrative_pool'] is False
    # Check if exclusion log was created
    assert os.path.exists(log_path)

def test_parse_csv_file(temp_dir, sample_lexicon):
    input_file = os.path.join(temp_dir, 'input.csv')
    output_file = os.path.join(temp_dir, 'output.csv')
    
    with open(input_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['author', 'year', 'tract', 'r', 'n', 'notes'])
        writer.writerow(['Test', 2023, 'arcuate fasciculus', 0.3, 20, 'notes'])
    
    # Mock nlp_logic
    import extraction.nlp_logic
    extraction.nlp_logic.extract_tract_descriptors = MagicMock(return_value=[])
    
    studies = parse_csv_file(input_file, sample_lexicon, None)
    assert len(studies) == 1
    assert studies[0]['author'] == 'Test'

def test_save_extracted_studies(temp_dir):
    studies = [
        {'author': 'A', 'year': 2020, 'tract': 't1', 'r': 0.1, 'n': 10, 'qualitative_desc': '', 'narrative_pool': False, 'source': 'raw'},
        {'author': 'B', 'year': 2021, 'tract': 't2', 'r': None, 'n': None, 'qualitative_desc': 'desc', 'narrative_pool': True, 'source': 'nlp'}
    ]
    output_file = os.path.join(temp_dir, 'output.csv')
    save_extracted_studies(studies, output_file)
    
    assert os.path.exists(output_file)
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]['author'] == 'A'
        assert rows[1]['narrative_pool'] == 'True' # CSV writes booleans as strings
