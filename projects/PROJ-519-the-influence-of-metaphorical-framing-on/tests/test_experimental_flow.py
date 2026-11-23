"""
Integration test for full experimental flow: assignment -> exposure -> scoring.

This test verifies that:
1. Participants are correctly assigned to conditions (Battle, Journey, Medical).
2. The correct vignette text is exposed based on the assigned condition.
3. CAMI scores and help-seeking Likert scores are computed correctly.
4. There is no text leakage between conditions.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json
import hashlib

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from data_models import Participant, Vignette
from vignette_engine import generate_vignettes, get_vignette_for_condition
from cami_scoring import compute_cami_score, compute_help_seeking_score
from experiment_runner import assign_conditions

# Constants for test data
TEST_PARTICIPANT_IDS = ["P001", "P002", "P003", "P004", "P005"]
CONDITIONS = ["Battle", "Journey", "Medical"]

# Mock survey response data structure
def create_mock_survey_responses(participant_id: str, condition: str) -> dict:
    """
    Create a mock survey response for a participant.
    
    Args:
        participant_id: The ID of the participant
        condition: The assigned condition (Battle, Journey, Medical)
        
    Returns:
        A dictionary representing the survey response
    """
    # Mock CAMI scale responses (1-5 Likert scale)
    # These are fixed values to ensure deterministic testing
    cami_responses = {
        "q1": 3, "q2": 4, "q3": 2, "q4": 3, "q5": 4,
        "q6": 3, "q7": 2, "q8": 4, "q9": 3, "q10": 4,
        "q11": 3, "q12": 4, "q13": 2, "q14": 3, "q15": 4,
        "q16": 3, "q17": 4, "q18": 2, "q19": 3, "q20": 4,
        "q21": 3, "q22": 4, "q23": 2, "q24": 3, "q25": 4,
        "q26": 3, "q27": 4, "q28": 2, "q29": 3, "q30": 4
    }
    
    # Mock help-seeking Likert (1-5)
    help_seeking_response = 4
    
    return {
        "participant_id": participant_id,
        "condition": condition,
        "raw_responses": cami_responses,
        "help_seeking": help_seeking_response,
        "attention_check_passed": True
    }

def test_assignment_exposure_scoring_flow():
    """
    Test the full experimental flow:
    1. Assign participants to conditions
    2. Expose them to the correct vignette
    3. Compute CAMI and help-seeking scores
    4. Verify no text leakage between conditions
    """
    # Step 1: Create mock participants
    participants = [Participant(pid) for pid in TEST_PARTICIPANT_IDS]
    
    # Step 2: Assign conditions
    assignments = assign_conditions(participants)
    
    # Verify assignments are valid
    assert len(assignments) == len(participants)
    for assignment in assignments:
        assert assignment["participant_id"] in TEST_PARTICIPANT_IDS
        assert assignment["condition"] in CONDITIONS
    
    # Step 3: Generate vignettes
    vignettes = generate_vignettes()
    assert len(vignettes) == 3
    assert all(cond in vignettes for cond in CONDITIONS)
    
    # Step 4: Expose participants to vignettes and collect responses
    survey_responses = []
    for assignment in assignments:
        participant_id = assignment["participant_id"]
        condition = assignment["condition"]
        
        # Get the correct vignette for the condition
        vignette_text = get_vignette_for_condition(condition, vignettes)
        assert vignette_text is not None, f"No vignette found for condition {condition}"
        
        # Verify no text leakage (check that the vignette text contains the correct metaphor)
        if condition == "Battle":
            assert "battle" in vignette_text.lower() or "fight" in vignette_text.lower()
            assert "journey" not in vignette_text.lower() or "path" not in vignette_text.lower()
        elif condition == "Journey":
            assert "journey" in vignette_text.lower() or "path" in vignette_text.lower()
            assert "battle" not in vignette_text.lower() or "fight" not in vignette_text.lower()
        elif condition == "Medical":
            # Medical condition should be neutral, no strong metaphors
            assert "battle" not in vignette_text.lower() or "fight" not in vignette_text.lower()
            assert "journey" not in vignette_text.lower() or "path" not in vignette_text.lower()
        
        # Create mock survey response
        response = create_mock_survey_responses(participant_id, condition)
        survey_responses.append(response)
    
    # Step 5: Compute scores
    results = []
    for response in survey_responses:
        participant_id = response["participant_id"]
        condition = response["condition"]
        raw_responses = response["raw_responses"]
        help_seeking = response["help_seeking"]
        
        # Compute CAMI score
        cami_score = compute_cami_score(raw_responses)
        assert cami_score is not None, "CAMI score computation failed"
        assert 0 <= cami_score <= 5, f"CAMI score {cami_score} out of range"
        
        # Compute help-seeking score
        help_seeking_score = compute_help_seeking_score(help_seeking)
        assert help_seeking_score is not None, "Help-seeking score computation failed"
        assert 1 <= help_seeking_score <= 5, f"Help-seeking score {help_seeking_score} out of range"
        
        results.append({
            "participant_id": participant_id,
            "condition": condition,
            "cami_score": cami_score,
            "help_seeking_score": help_seeking_score
        })
    
    # Step 6: Verify results
    assert len(results) == len(TEST_PARTICIPANT_IDS)
    
    # Check that each participant has a result
    result_ids = [r["participant_id"] for r in results]
    assert all(pid in result_ids for pid in TEST_PARTICIPANT_IDS)
    
    # Check that conditions are correctly associated with scores
    for result in results:
        assert result["condition"] in CONDITIONS
        assert result["cami_score"] is not None
        assert result["help_seeking_score"] is not None

def test_vignette_text_integrity():
    """
    Test that vignette texts are distinct and do not leak between conditions.
    """
    vignettes = generate_vignettes()
    
    # Check that each condition has a unique vignette
    vignette_texts = [vignettes[cond] for cond in CONDITIONS]
    assert len(set(vignette_texts)) == 3, "Vignette texts are not unique"
    
    # Check for metaphor leakage
    for condition, text in vignettes.items():
        text_lower = text.lower()
        
        if condition == "Battle":
            # Should contain battle-related terms
            assert any(term in text_lower for term in ["battle", "fight", "war", "struggle"])
            # Should NOT contain journey-related terms
            assert not any(term in text_lower for term in ["journey", "path", "walk"])
        elif condition == "Journey":
            # Should contain journey-related terms
            assert any(term in text_lower for term in ["journey", "path", "walk", "road"])
            # Should NOT contain battle-related terms
            assert not any(term in text_lower for term in ["battle", "fight", "war", "struggle"])
        elif condition == "Medical":
            # Should be neutral, no strong metaphors
            assert not any(term in text_lower for term in ["battle", "fight", "war", "struggle", "journey", "path", "walk"])

def test_scoring_consistency():
    """
    Test that scoring functions produce consistent results for the same inputs.
    """
    # Create a fixed set of raw responses
    fixed_responses = {
        "q1": 3, "q2": 4, "q3": 2, "q4": 3, "q5": 4,
        "q6": 3, "q7": 2, "q8": 4, "q9": 3, "q10": 4,
        "q11": 3, "q12": 4, "q13": 2, "q14": 3, "q15": 4,
        "q16": 3, "q17": 4, "q18": 2, "q19": 3, "q20": 4,
        "q21": 3, "q22": 4, "q23": 2, "q24": 3, "q25": 4,
        "q26": 3, "q27": 4, "q28": 2, "q29": 3, "q30": 4
    }
    
    # Compute CAMI score multiple times
    scores = [compute_cami_score(fixed_responses) for _ in range(5)]
    assert len(set(scores)) == 1, "CAMI scores are not consistent"
    
    # Compute help-seeking score multiple times
    help_seeking_scores = [compute_help_seeking_score(4) for _ in range(5)]
    assert len(set(help_seeking_scores)) == 1, "Help-seeking scores are not consistent"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
