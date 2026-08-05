import pytest
import csv
import json
import yaml
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from extraction.parser import parse_row, log_exclusion, save_extracted_studies, load_tract_lexicon
from utils.logger import get_logger

logger = get_logger(__name__)

@pytest.fixture
def mock_lexicon():
    """Create a temporary lexicon file for testing."""
    lexicon = {
        "tracts": ["arcuate fasciculus", "cingulum bundle", "uncinate fasciculus", "inferior longitudinal fasciculus", "auditory cortex", "ventral striatum"],
        "directional_verbs": ["increased", "decreased", "correlated", "associated with"]
    }
    # We assume the lexicon file exists in data/config as per T007c
    # For unit testing, we might need to mock the file or ensure it exists.
    # In a real CI, T007c runs before. Here we assume it exists or create it.
    lexicon_path = Path("data/config/tract_lexicon.yaml")
    lexicon_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lexicon_path, 'w') as f:
        yaml.dump(lexicon, f)
    return lexicon

@pytest.fixture
def mock_row_complete():
    return {
        "id": "S001",
        "author": "Smith",
        "year": "2020",
        "tract": "arcuate fasciculus",
        "r": "0.45",
        "n": "50",
        "p": "0.01",
        "notes": "Strong correlation."
    }

@pytest.fixture
def mock_row_missing_r():
    return {
        "id": "S002",
        "author": "Doe",
        "year": "2019",
        "tract": "cingulum bundle",
        "r": "",
        "n": "30",
        "p": "0.03",
        "notes": "Significant finding."
    }

@pytest.fixture
def mock_row_text_only():
    return {
        "id": "S003",
        "author": "Lee",
        "year": "2021",
        "tract": "",
        "r": "",
        "n": "",
        "p": "",
        "notes": "Increased connectivity observed in the uncinate fasciculus."
    }

def test_parse_complete_row(mock_lexicon, mock_row_complete):
    lexicon = load_tract_lexicon()
    result = parse_row(mock_row_complete, lexicon, "S001")
    
    assert result['r'] == 0.45
    assert result['n'] == 50
    assert result['narrative_pool'] == False
    assert result['qualitative_desc'] == "" # No NLP needed if r/n present and tract known

def test_parse_p_value_conversion(mock_lexicon, mock_row_missing_r):
    lexicon = load_tract_lexicon()
    result = parse_row(mock_row_missing_r, lexicon, "S002")
    
    # Should convert p=0.03 to r
    assert result['r'] is not None
    assert result['n'] == 30
    assert result['narrative_pool'] == False

def test_parse_text_only_narrative_pool(mock_lexicon, mock_row_text_only):
    lexicon = load_tract_lexicon()
    result = parse_row(mock_row_text_only, lexicon, "S003")
    
    assert result['narrative_pool'] == True
    assert result['qualitative_desc'] is not None
    # Check if tract was found
    assert result['tract'] == "uncinate fasciculus"

def test_log_exclusion(tmp_path):
    # Override log path for test
    import extraction.parser as parser_module
    original_logs_dir = parser_module.LOGS_DIR
    parser_module.LOGS_DIR = tmp_path / "logs"
    
    try:
        log_exclusion("S001", "missing_data", "r=, n=")
        
        log_path = parser_module.LOGS_DIR / "exclusion_log.csv"
        assert log_path.exists()
        
        with open(log_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]['study_id'] == 'S001'
            assert rows[0]['reason'] == 'missing_data'
    finally:
        parser_module.LOGS_DIR = original_logs_dir
