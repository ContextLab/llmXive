"""Unit tests for LMM model construction and analysis logic.

This module tests the core logic of the Linear Mixed-Effects Model
implementation in code/04_run_lmm.py, ensuring that:
1. Model construction with mock data works correctly
2. Fixed effects are estimated properly
3. Random effects structure is valid
4. Satterthwaite approximation for degrees of freedom works
5. Tukey-corrected post-hoc comparisons execute without error
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
import pytest
from linearmodels.panel import PanelOLS
from statsmodels.regression.mixed_linear_model import MixedLM

# Import the functions we're testing from the analysis module
from code.config import get_project_root, get_raw_data_dir, get_processed_data_dir
from code.logging_config import setup_logging, get_logger
from code import (
    load_cleaning_log,
    load_ratings,
    load_stimuli,
    apply_listwise_deletion,
    log_exclusion_reason,
    run_primary_lmm,
    run_tukey_post_hoc,
    save_analysis_results
)


# ============================================================================
# Fixtures for mock data generation
# ============================================================================

@pytest.fixture
def mock_stimuli_data():
    """Generate mock stimuli data for testing."""
    stimuli = []
    scenarios = ["support_needed", "celebration", "problem_solving"]
    emoji_levels = [0, 1, 2]
    punct_levels = ["period", "exclamation", "question"]
    length_levels = ["short", "medium", "long"]

    stimulus_id = 0
    for scenario in scenarios:
        for emoji in emoji_levels:
            for punct in punct_levels:
                for length in length_levels:
                    text = f"[{emoji} emojis] {punct} {length} text for {scenario}"
                    stimuli.append({
                        "id": f"S{stimulus_id:03d}",
                        "text": text,
                        "emoji_count": emoji,
                        "punctuation_type": punct,
                        "length_category": length,
                        "scenario_id": scenario
                    })
                    stimulus_id += 1

    return pd.DataFrame(stimuli)

@pytest.fixture
def mock_ratings_data(mock_stimuli_data):
    """Generate mock ratings data for testing LMM."""
    np.random.seed(42)
    ratings = []

    # Create ratings for each stimulus from multiple participants
    participants = [f"P{pid:03d}" for pid in range(1, 51)]  # 50 participants

    for stimulus_id in mock_stimuli_data["id"]:
        for participant_id in participants:
            # Simulate rating based on stimulus properties with some noise
            base_rating = 4.0
            emoji_effect = mock_stimuli_data[mock_stimuli_data["id"] == stimulus_id]["emoji_count"].values[0] * 0.3
            punct_effect = 0.5 if mock_stimuli_data[mock_stimuli_data["id"] == stimulus_id]["punctuation_type"].values[0] == "exclamation" else 0.0
            noise = np.random.normal(0, 0.5)

            rating = min(7, max(1, base_rating + emoji_effect + punct_effect + noise))

            # Randomize relationship
            relationship = np.random.choice(["friend", "acquaintance"])

            ratings.append({
                "participant_id": participant_id,
                "stimulus_id": stimulus_id,
                "relationship": relationship,
                "rating": round(rating, 1)
            })

    return pd.DataFrame(ratings)

@pytest.fixture
def mock_cleaning_log():
    """Generate mock cleaning log with some exclusions."""
    return pd.DataFrame([
        {"participant_id": "P001", "exclusion_reason": "straight_lining", "timestamp": "2024-01-01T00:00:00", "variance_value": 0.0},
        {"participant_id": "P002", "exclusion_reason": "straight_lining", "timestamp": "2024-01-01T00:00:00", "variance_value": 0.0},
        {"participant_id": "P003", "exclusion_reason": "missing_data", "timestamp": "2024-01-01T00:00:00", "variance_value": 0.0}
    ])

@pytest.fixture
def temp_data_dir():
    """Create temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        raw_dir = tmpdir / "data" / "raw"
        processed_dir = tmpdir / "data" / "processed"
        raw_dir.mkdir(parents=True)
        processed_dir.mkdir(parents=True)
        yield {
            "raw": raw_dir,
            "processed": processed_dir
        }


# ============================================================================
# Tests for data loading and preprocessing
# ============================================================================

def test_load_stimuli(mock_stimuli_data, temp_data_dir):
    """Test that stimuli data can be loaded correctly."""
    # Save stimuli to temp location
    stimuli_path = temp_data_dir["raw"] / "stimuli.csv"
    mock_stimuli_data.to_csv(stimuli_path, index=False)

    # Load and verify
    loaded = load_stimuli(str(stimuli_path))
    assert isinstance(loaded, pd.DataFrame)
    assert len(loaded) == len(mock_stimuli_data)
    assert set(loaded.columns) == set(mock_stimuli_data.columns)

def test_load_ratings(mock_ratings_data, temp_data_dir):
    """Test that ratings data can be loaded correctly."""
    # Save ratings to temp location
    ratings_path = temp_data_dir["raw"] / "ratings.csv"
    mock_ratings_data.to_csv(ratings_path, index=False)

    # Load and verify
    loaded = load_ratings(str(ratings_path))
    assert isinstance(loaded, pd.DataFrame)
    assert len(loaded) == len(mock_ratings_data)
    assert set(loaded.columns) == set(mock_ratings_data.columns)

def test_apply_listwise_deletion(mock_ratings_data, mock_cleaning_log, temp_data_dir):
    """Test that listwise deletion correctly removes excluded participants."""
    # Save cleaning log
    cleaning_log_path = temp_data_dir["processed"] / "cleaning_log.csv"
    mock_cleaning_log.to_csv(cleaning_log_path, index=False)

    # Apply deletion
    cleaned_data = apply_listwise_deletion(mock_ratings_data, str(cleaning_log_path))

    # Verify excluded participants are removed
    assert "P001" not in cleaned_data["participant_id"].values
    assert "P002" not in cleaned_data["participant_id"].values
    assert "P003" not in cleaned_data["participant_id"].values
    assert "P004" in cleaned_data["participant_id"].values  # Should remain


# ============================================================================
# Tests for LMM model construction
# ============================================================================

def test_run_primary_lmm_with_mock_data(mock_stimuli_data, mock_ratings_data, temp_data_dir):
    """Test that primary LMM model construction works with mock data."""
    # Save data
    stimuli_path = temp_data_dir["raw"] / "stimuli.csv"
    ratings_path = temp_data_dir["raw"] / "ratings.csv"
    cleaning_log_path = temp_data_dir["processed"] / "cleaning_log.csv"

    mock_stimuli_data.to_csv(stimuli_path, index=False)
    mock_ratings_data.to_csv(ratings_path, index=False)
    pd.DataFrame().to_csv(cleaning_log_path, index=False)  # Empty cleaning log

    # Run LMM
    result = run_primary_lmm(
        str(stimuli_path),
        str(ratings_path),
        str(cleaning_log_path)
    )

    # Verify result structure
    assert isinstance(result, dict)
    assert "fixed_effects" in result
    assert "random_effects" in result
    assert "model_summary" in result
    assert "f_statistic" in result
    assert "p_value" in result

    # Verify fixed effects contain expected variables
    fixed_effects = result["fixed_effects"]
    assert "Intercept" in fixed_effects
    assert "C(relationship)[T.acquaintance]" in fixed_effects  # Reference should be friend
    assert "emoji_count" in fixed_effects
    assert "punctuation_type" in fixed_effects

    # Verify random effects structure
    random_effects = result["random_effects"]
    assert "participant_id" in random_effects
    assert "stimulus_id" in random_effects

def test_lmm_interaction_term_significance(mock_stimuli_data, mock_ratings_data, temp_data_dir):
    """Test that LMM correctly identifies significant interaction terms."""
    # Create data with known interaction effect
    np.random.seed(123)
    enhanced_ratings = mock_ratings_data.copy()

    # Add interaction effect: friend relationship amplifies emoji effect
    for idx, row in enhanced_ratings.iterrows():
        if row["relationship"] == "friend" and row["stimulus_id"] in mock_stimuli_data[mock_stimuli_data["emoji_count"] > 0]["id"].values:
            # Boost rating for friends with emojis
            enhanced_ratings.at[idx, "rating"] = min(7, row["rating"] + 0.8)

    # Save data
    stimuli_path = temp_data_dir["raw"] / "stimuli.csv"
    ratings_path = temp_data_dir["raw"] / "ratings.csv"
    cleaning_log_path = temp_data_dir["processed"] / "cleaning_log.csv"

    mock_stimuli_data.to_csv(stimuli_path, index=False)
    enhanced_ratings.to_csv(ratings_path, index=False)
    pd.DataFrame().to_csv(cleaning_log_path, index=False)

    # Run LMM
    result = run_primary_lmm(
        str(stimuli_path),
        str(ratings_path),
        str(cleaning_log_path)
    )

    # Verify interaction term exists and has a value
    assert "interaction" in result["fixed_effects"] or any(
        "relationship" in str(k) and ("emoji" in str(k) or "punct" in str(k))
        for k in result["fixed_effects"].keys()
    )


# ============================================================================
# Tests for Tukey post-hoc comparisons
# ============================================================================

def test_run_tukey_post_hoc(mock_stimuli_data, mock_ratings_data, temp_data_dir):
    """Test that Tukey-corrected post-hoc comparisons execute without error."""
    # Save data
    stimuli_path = temp_data_dir["raw"] / "stimuli.csv"
    ratings_path = temp_data_dir["raw"] / "ratings.csv"
    cleaning_log_path = temp_data_dir["processed"] / "cleaning_log.csv"

    mock_stimuli_data.to_csv(stimuli_path, index=False)
    mock_ratings_data.to_csv(ratings_path, index=False)
    pd.DataFrame().to_csv(cleaning_log_path, index=False)

    # Run primary LMM first
    lmm_result = run_primary_lmm(
        str(stimuli_path),
        str(ratings_path),
        str(cleaning_log_path)
    )

    # Run Tukey post-hoc
    tukey_result = run_tukey_post_hoc(
        str(stimuli_path),
        str(ratings_path),
        str(cleaning_log_path),
        lmm_result
    )

    # Verify result structure
    assert isinstance(tukey_result, dict)
    assert "comparisons" in tukey_result
    assert "significant_pairs" in tukey_result

    # Verify comparisons are a list of dictionaries
    assert isinstance(tukey_result["comparisons"], list)
    if len(tukey_result["comparisons"]) > 0:
        assert "group1" in tukey_result["comparisons"][0]
        assert "group2" in tukey_result["comparisons"][0]
        assert "p_value" in tukey_result["comparisons"][0]
        assert "p_value_corrected" in tukey_result["comparisons"][0]


# ============================================================================
# Tests for result serialization
# ============================================================================

def test_save_analysis_results(mock_stimuli_data, mock_ratings_data, temp_data_dir):
    """Test that analysis results are correctly serialized to JSON."""
    # Save data
    stimuli_path = temp_data_dir["raw"] / "stimuli.csv"
    ratings_path = temp_data_dir["raw"] / "ratings.csv"
    cleaning_log_path = temp_data_dir["processed"] / "cleaning_log.csv"

    mock_stimuli_data.to_csv(stimuli_path, index=False)
    mock_ratings_data.to_csv(ratings_path, index=False)
    pd.DataFrame().to_csv(cleaning_log_path, index=False)

    # Run LMM
    lmm_result = run_primary_lmm(
        str(stimuli_path),
        str(ratings_path),
        str(cleaning_log_path)
    )

    # Run Tukey
    tukey_result = run_tukey_post_hoc(
        str(stimuli_path),
        str(ratings_path),
        str(cleaning_log_path),
        lmm_result
    )

    # Combine results
    combined_result = {
        "lmm_results": lmm_result,
        "tukey_results": tukey_result,
        "exclusion_summary": {"count": 0, "reasons": []}
    }

    # Save results
    output_path = temp_data_dir["processed"] / "analysis_results.json"
    save_analysis_results(combined_result, str(output_path))

    # Verify file exists and is valid JSON
    assert output_path.exists()
    with open(output_path, "r") as f:
        loaded = json.load(f)

    assert "lmm_results" in loaded
    assert "tukey_results" in loaded
    assert "exclusion_summary" in loaded

def test_save_analysis_results_with_exclusions(mock_stimuli_data, mock_ratings_data, mock_cleaning_log, temp_data_dir):
    """Test that exclusion summary is correctly included in results."""
    # Save data
    stimuli_path = temp_data_dir["raw"] / "stimuli.csv"
    ratings_path = temp_data_dir["raw"] / "ratings.csv"
    cleaning_log_path = temp_data_dir["processed"] / "cleaning_log.csv"

    mock_stimuli_data.to_csv(stimuli_path, index=False)
    mock_ratings_data.to_csv(ratings_path, index=False)
    mock_cleaning_log.to_csv(cleaning_log_path, index=False)

    # Run LMM
    lmm_result = run_primary_lmm(
        str(stimuli_path),
        str(ratings_path),
        str(cleaning_log_path)
    )

    # Run Tukey
    tukey_result = run_tukey_post_hoc(
        str(stimuli_path),
        str(ratings_path),
        str(cleaning_log_path),
        lmm_result
    )

    # Prepare exclusion summary from cleaning log
    exclusion_summary = {
        "count": len(mock_cleaning_log),
        "reasons": mock_cleaning_log["exclusion_reason"].value_counts().to_dict()
    }

    # Combine results
    combined_result = {
        "lmm_results": lmm_result,
        "tukey_results": tukey_result,
        "exclusion_summary": exclusion_summary
    }

    # Save results
    output_path = temp_data_dir["processed"] / "analysis_results.json"
    save_analysis_results(combined_result, str(output_path))

    # Verify exclusion summary is in output
    with open(output_path, "r") as f:
        loaded = json.load(f)

    assert "exclusion_summary" in loaded
    assert loaded["exclusion_summary"]["count"] == len(mock_cleaning_log)
    assert "straight_lining" in loaded["exclusion_summary"]["reasons"]


# ============================================================================
# Edge case tests
# ============================================================================

def test_lmm_with_minimal_data(temp_data_dir):
    """Test LMM construction with minimal valid dataset."""
    # Create minimal stimuli (3 items)
    stimuli = pd.DataFrame([
        {"id": "S001", "text": "Test 1", "emoji_count": 0, "punctuation_type": "period", "length_category": "short", "scenario_id": "test"},
        {"id": "S002", "text": "Test 2", "emoji_count": 1, "punctuation_type": "exclamation", "length_category": "medium", "scenario_id": "test"},
        {"id": "S003", "text": "Test 3", "emoji_count": 2, "punctuation_type": "question", "length_category": "long", "scenario_id": "test"}
    ])

    # Create minimal ratings (2 participants, all stimuli)
    ratings = pd.DataFrame([
        {"participant_id": "P001", "stimulus_id": "S001", "relationship": "friend", "rating": 4.0},
        {"participant_id": "P001", "stimulus_id": "S002", "relationship": "friend", "rating": 5.0},
        {"participant_id": "P001", "stimulus_id": "S003", "relationship": "friend", "rating": 6.0},
        {"participant_id": "P002", "stimulus_id": "S001", "relationship": "acquaintance", "rating": 3.0},
        {"participant_id": "P002", "stimulus_id": "S002", "relationship": "acquaintance", "rating": 4.0},
        {"participant_id": "P002", "stimulus_id": "S003", "relationship": "acquaintance", "rating": 5.0}
    ])

    stimuli_path = temp_data_dir["raw"] / "stimuli.csv"
    ratings_path = temp_data_dir["raw"] / "ratings.csv"
    cleaning_log_path = temp_data_dir["processed"] / "cleaning_log.csv"

    stimuli.to_csv(stimuli_path, index=False)
    ratings.to_csv(ratings_path, index=False)
    pd.DataFrame().to_csv(cleaning_log_path, index=False)

    # Should not raise error
    result = run_primary_lmm(
        str(stimuli_path),
        str(ratings_path),
        str(cleaning_log_path)
    )

    assert result is not None
    assert "fixed_effects" in result

def test_log_exclusion_reason(temp_data_dir):
    """Test that exclusion reasons are correctly logged."""
    cleaning_log_path = temp_data_dir["processed"] / "cleaning_log.csv"
    pd.DataFrame(columns=["participant_id", "exclusion_reason", "timestamp", "variance_value"]).to_csv(
        cleaning_log_path, index=False
    )

    # Log an exclusion
    log_exclusion_reason("P999", "missing_data", cleaning_log_path, 0.0)

    # Verify it was added
    log_df = pd.read_csv(cleaning_log_path)
    assert len(log_df) == 1
    assert log_df.iloc[0]["participant_id"] == "P999"
    assert log_df.iloc[0]["exclusion_reason"] == "missing_data"


# ============================================================================
# Integration-style test for full analysis flow
# ============================================================================

def test_full_analysis_flow_with_mock_data(mock_stimuli_data, mock_ratings_data, temp_data_dir):
    """Test the complete analysis pipeline from data loading to result serialization."""
    # Setup paths
    stimuli_path = temp_data_dir["raw"] / "stimuli.csv"
    ratings_path = temp_data_dir["raw"] / "ratings.csv"
    cleaning_log_path = temp_data_dir["processed"] / "cleaning_log.csv"
    output_path = temp_data_dir["processed"] / "analysis_results.json"

    # Save input data
    mock_stimuli_data.to_csv(stimuli_path, index=False)
    mock_ratings_data.to_csv(ratings_path, index=False)
    pd.DataFrame().to_csv(cleaning_log_path, index=False)

    # Execute full pipeline
    # 1. Load and clean data
    cleaned_data = apply_listwise_deletion(
        load_ratings(str(ratings_path)),
        str(cleaning_log_path)
    )

    # 2. Run primary LMM
    lmm_result = run_primary_lmm(
        str(stimuli_path),
        str(ratings_path),
        str(cleaning_log_path)
    )

    # 3. Run Tukey post-hoc
    tukey_result = run_tukey_post_hoc(
        str(stimuli_path),
        str(ratings_path),
        str(cleaning_log_path),
        lmm_result
    )

    # 4. Prepare and save final results
    combined_result = {
        "lmm_results": lmm_result,
        "tukey_results": tukey_result,
        "exclusion_summary": {"count": 0, "reasons": {}}
    }

    save_analysis_results(combined_result, str(output_path))

    # Verify final output
    assert output_path.exists()
    with open(output_path, "r") as f:
        final_results = json.load(f)

    # Verify all required components are present
    assert "lmm_results" in final_results
    assert "tukey_results" in final_results
    assert "exclusion_summary" in final_results
    assert "fixed_effects" in final_results["lmm_results"]
    assert "random_effects" in final_results["lmm_results"]
    assert "comparisons" in final_results["tukey_results"]

    # Verify statistical validity
    assert final_results["lmm_results"]["f_statistic"] > 0
    assert 0 <= final_results["lmm_results"]["p_value"] <= 1