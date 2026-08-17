"""
Tests for the Survey Interface Module (T013b).
"""
import json
import os
import csv
import tempfile
import pytest
from datetime import datetime

# Ensure project root is in path
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.survey_interface import (
    SurveyResponse,
    load_assignments,
    save_responses,
    run_cli_survey_simulation
)


@pytest.fixture
def sample_assignments_csv(tmp_path):
    """Create a temporary CSV file with sample assignments."""
    csv_path = tmp_path / "experimental_assignments.csv"
    data = [
        {"participant_id": "P001", "condition": "Battle", "age": 24, "gender": "F"},
        {"participant_id": "P002", "condition": "Journey", "age": 33, "gender": "M"},
        {"participant_id": "P003", "condition": "Medical", "age": 18, "gender": "F"}
    ]
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    return str(csv_path)


@pytest.fixture
def sample_survey_output(tmp_path):
    """Path for output JSON."""
    return str(tmp_path / "survey_responses.json")


def test_survey_response_dataclass():
    """Test that SurveyResponse dataclass initializes correctly."""
    response = SurveyResponse(
        participant_id="P001",
        condition="Battle",
        cami_items={"item_1": 3, "item_2": 4},
        help_seeking_intent=5,
        attention_check=5,
        condition_guess="Battle"
    )
    assert response.participant_id == "P001"
    assert response.condition == "Battle"
    assert response.cami_items["item_1"] == 3
    assert response.timestamp is not None


def test_load_assignments_valid_csv(sample_assignments_csv):
    """Test loading assignments from a valid CSV."""
    assignments = load_assignments(sample_assignments_csv)
    assert len(assignments) == 3
    assert assignments[0]["participant_id"] == "P001"
    assert assignments[0]["condition"] == "Battle"


def test_load_assignments_missing_file():
    """Test that loading from a missing file raises an error."""
    with pytest.raises(FileNotFoundError):
        load_assignments("nonexistent.csv")


def test_save_responses_creates_valid_json(sample_assignments_csv, sample_survey_output):
    """Test that saving responses creates a valid JSON file with correct structure."""
    # Run simulation to generate data
    run_cli_survey_simulation(sample_assignments_csv, sample_survey_output)
    
    assert os.path.exists(sample_survey_output)
    
    with open(sample_survey_output, 'r') as f:
        data = json.load(f)
    
    assert "responses" in data
    assert "metadata" in data
    assert len(data["responses"]) == 3
    
    # Check structure of first response
    first_resp = data["responses"][0]
    assert "participant_id" in first_resp
    assert "condition" in first_resp
    assert "cami_items" in first_resp
    assert "help_seeking_intent" in first_resp
    assert "attention_check" in first_resp
    assert "condition_guess" in first_resp


def test_survey_output_schema_integrity(sample_assignments_csv, sample_survey_output):
    """Test that the output JSON adheres to the expected schema for T014."""
    run_cli_survey_simulation(sample_assignments_csv, sample_survey_output)
    
    with open(sample_survey_output, 'r') as f:
        data = json.load(f)
    
    for resp in data["responses"]:
        # Validate CAMI items are integers 1-5
        for key, val in resp["cami_items"].items():
            assert isinstance(val, int)
            assert 1 <= val <= 5
        
        # Validate help seeking is 1-7
        assert isinstance(resp["help_seeking_intent"], int)
        assert 1 <= resp["help_seeking_intent"] <= 7
        
        # Validate attention check is 1-5
        assert isinstance(resp["attention_check"], int)
        assert 1 <= resp["attention_check"] <= 5
