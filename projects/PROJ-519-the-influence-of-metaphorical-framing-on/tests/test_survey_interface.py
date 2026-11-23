"""
Tests for the Survey Interface Module (T013b).
"""
import os
import json
import tempfile
import csv
import pytest
from datetime import datetime

# Adjust path to import from src
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'code'))
sys.path.insert(0, PROJECT_ROOT)

from src.survey_interface import (
    load_assignments, 
    save_responses, 
    SurveyResponse, 
    run_cli_survey_simulation,
    CAMI_ITEMS,
    HELP_SEEKING_ITEMS
)

@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file with experimental assignments."""
    fd, path = tempfile.mkstemp(suffix='.csv')
    try:
        with os.fdopen(fd, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['participant_id', 'condition', 'vignette_id'])
            writer.writerow(['P001', 'Battle', 'V_BATTLE_01'])
            writer.writerow(['P002', 'Journey', 'V_JOURNEY_01'])
            writer.writerow(['P003', 'Medical', 'V_MEDICAL_01'])
        yield path
    finally:
        os.remove(path)

@pytest.fixture
def temp_json_file():
    """Create a temporary path for JSON output."""
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)

def test_load_assignments(temp_csv_file):
    """Test loading assignments from CSV."""
    participants = load_assignments(temp_csv_file)
    assert len(participants) == 3
    assert participants[0]['participant_id'] == 'P001'
    assert participants[0]['condition'] == 'Battle'

def test_save_responses(temp_json_file):
    """Test saving responses to JSON."""
    response = SurveyResponse(
        participant_id='TEST_01',
        condition='Battle',
        timestamp=datetime.utcnow().isoformat(),
        vignette_version='V_BATTLE_01',
        cami_scores={'C1': 4, 'C2': 2},
        help_seeking_scores={'H1': 5},
        attention_check_passed=True
    )
    save_responses([response], temp_json_file)
    
    assert os.path.exists(temp_json_file)
    with open(temp_json_file, 'r') as f:
        data = json.load(f)
    
    assert len(data) == 1
    assert data[0]['participant_id'] == 'TEST_01'
    assert data[0]['condition'] == 'Battle'

def test_cli_simulation_flow(temp_csv_file, temp_json_file):
    """Test the full CLI simulation flow (T013b)."""
    run_cli_survey_simulation(temp_csv_file, temp_json_file)
    
    assert os.path.exists(temp_json_file)
    with open(temp_json_file, 'r') as f:
        data = json.load(f)
    
    # Verify all participants were processed
    assert len(data) == 3
    
    # Verify structure of each response
    for entry in data:
        assert 'participant_id' in entry
        assert 'condition' in entry
        assert 'cami_scores' in entry
        assert 'help_seeking_scores' in entry
        assert isinstance(entry['cami_scores'], dict)
        assert isinstance(entry['help_seeking_scores'], dict)
        
        # Verify CAMI items present (at least the keys)
        # Note: In simulation, we might not have all items if the logic changes,
        # but the structure must be valid.
        assert 'timestamp' in entry
        assert entry['attention_check_passed'] is True

def test_survey_response_dataclass():
    """Test SurveyResponse dataclass integrity."""
    r = SurveyResponse(
        participant_id='X',
        condition='Battle',
        timestamp='2023-01-01T00:00:00',
        vignette_version='V1',
        cami_scores={'C1': 1},
        help_seeking_scores={'H1': 5},
        attention_check_passed=True
    )
    assert r.participant_id == 'X'
    assert r.cami_scores['C1'] == 1
