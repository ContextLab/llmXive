"""
Tests for the CAMI Scoring Module.
"""
import json
import os
import tempfile
import pytest
from src.cami_scoring import (
    load_survey_responses, 
    process_responses, 
    save_scores,
    reverse_score,
    SUBSCALE_ITEMS,
    REVERSE_ITEMS
)

def test_reverse_score():
    assert reverse_score(1) == 4
    assert reverse_score(2) == 3
    assert reverse_score(3) == 2
    assert reverse_score(4) == 1

def create_mock_survey_data(participant_count=3):
    """Generates valid mock survey data for testing."""
    responses = []
    for i in range(participant_count):
        p_id = f"p_{i}"
        # Generate 40 valid responses (1-4)
        q_data = {f"q{j}": ((j + i) % 4) + 1 for j in range(1, 41)}
        
        # Add help seeking intent (1-7)
        q_data["help_seeking_intent"] = 5 + i
        
        # Add attention check
        q_data["attention_check"] = "correct"

        responses.append({
            "participant_id": p_id,
            "condition": "Battle" if i % 2 == 0 else "Journey",
            "timestamp": "2023-10-27T10:00:00",
            "responses": q_data
        })
    return responses

def test_process_responses_valid():
    data = create_mock_survey_data(1)
    result = process_responses(data)
    
    assert len(result) == 1
    assert result[0]["participant_id"] == "p_0"
    assert "authoritarianism" in result[0]
    assert "benevolence" in result[0]
    assert "social_restrictiveness" in result[0]
    assert "community_mental_health" in result[0]
    assert result[0]["help_seeking_intent"] == 5
    assert result[0]["attention_failed"] is False

def test_process_responses_missing_data():
    """Test that records with missing CAMI items are skipped."""
    data = create_mock_survey_data(1)
    # Remove a required item
    del data[0]["responses"]["q1"]
    
    result = process_responses(data)
    # Should be empty because the only record was invalid
    assert len(result) == 0

def test_process_responses_attention_fail():
    """Test that attention check failures are flagged."""
    data = create_mock_survey_data(1)
    data[0]["responses"]["attention_check"] = "incorrect"
    
    result = process_responses(data)
    assert len(result) == 1
    assert result[0]["attention_failed"] is True

def test_save_and_load_scores():
    """Test full round trip: process -> save -> load."""
    data = create_mock_survey_data(2)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = os.path.join(tmpdir, "input.json")
        output_file = os.path.join(tmpdir, "output.csv")
        
        # Save input
        with open(input_file, 'w') as f:
            json.dump(data, f)
        
        # Process
        processed = process_responses(load_survey_responses(input_file))
        
        # Save output
        save_scores(processed, output_file)
        
        # Verify file exists and has content
        assert os.path.exists(output_file)
        with open(output_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 3 # Header + 2 data rows
        assert "participant_id" in lines[0]

def test_missing_help_seeking():
    """Test that missing help-seeking intent causes skip."""
    data = create_mock_survey_data(1)
    del data[0]["responses"]["help_seeking_intent"]
    
    result = process_responses(data)
    assert len(result) == 0

def test_invalid_input_file():
    """Test loading from a non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_survey_responses("non_existent_file.json")

def test_invalid_json_structure():
    """Test loading a JSON file that isn't a list."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"not": "a list"}, f)
        f.flush()
        with pytest.raises(ValueError):
            load_survey_responses(f.name)
        os.unlink(f.name)