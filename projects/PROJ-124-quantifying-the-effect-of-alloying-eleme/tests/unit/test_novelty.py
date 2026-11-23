"""
Unit tests for the novelty check utilities.
"""
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import os

# Import the module under test
# Adjust import path based on project structure
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.novelty import (
    load_known_alloys,
    normalize_composition,
    compositions_match,
    check_novelty,
    batch_check_novelty
)

@pytest.fixture
def sample_known_alloys():
    """Create a temporary CSV with sample known alloys."""
    data = {
        'composition': ['Fe50Co50', 'Cu60Zr40', 'Ti50Ni50', 'Zr55Al10Cu30Ni5'],
        'source': ['test', 'test', 'test', 'test']
    }
    df = pd.DataFrame(data)
    return df

@pytest.fixture
def temp_known_alloys_file(sample_known_alloys):
    """Create a temporary file for the known alloys CSV."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_known_alloys.to_csv(f, index=False)
        temp_path = Path(f.name)
    yield temp_path
    os.unlink(temp_path)

def test_normalize_composition():
    """Test that composition normalization works correctly."""
    assert normalize_composition("Fe 50 Co 50") == "FE50CO50"
    assert normalize_composition("fe50co50") == "FE50CO50"
    assert normalize_composition("  Cu60Zr40  ") == "CU60ZR40"

def test_compositions_match():
    """Test that composition matching logic is correct."""
    assert compositions_match("Fe50Co50", "Fe50Co50") is True
    assert compositions_match("Fe50Co50", "FE50CO50") is True
    assert compositions_match("Fe50Co50", "Co50Fe50") is False  # Order matters in simple string match
    assert compositions_match("Fe50Co50", "Fe60Co40") is False

def test_check_novelty_known(temp_known_alloys_file):
    """Test that known compositions are identified correctly."""
    df = load_known_alloys(temp_known_alloys_file)
    status = check_novelty("Fe50Co50", df)
    assert status == "known"

def test_check_novelty_novel(temp_known_alloys_file):
    """Test that novel compositions are identified correctly."""
    df = load_known_alloys(temp_known_alloys_file)
    status = check_novelty("Au100", df)
    assert status == "novel"

def test_check_novelty_missing_file():
    """Test behavior when known alloys file is missing."""
    df = load_known_alloys(Path("/nonexistent/path.csv"))
    assert df is None
    
    status = check_novelty("AnyComposition", df)
    assert status == "unverified_external"

def test_batch_check_novelty(temp_known_alloys_file):
    """Test batch novelty checking."""
    df = load_known_alloys(temp_known_alloys_file)
    comps = ["Fe50Co50", "Au100", "Cu60Zr40", "Unknown"]
    statuses = batch_check_novelty(comps, df)
    
    assert statuses[0] == "known"
    assert statuses[1] == "novel"
    assert statuses[2] == "known"
    assert statuses[3] == "novel"

def test_batch_check_novelty_missing_file():
    """Test batch novelty checking with missing file."""
    comps = ["Fe50Co50", "Au100"]
    statuses = batch_check_novelty(comps, None)
    
    assert all(s == "unverified_external" for s in statuses)
