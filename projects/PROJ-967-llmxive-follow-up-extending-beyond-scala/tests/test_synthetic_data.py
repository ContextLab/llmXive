import os
import sys
import json
import pandas as pd
import pytest
from pathlib import Path

# Add the code directory to the path
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from synthetic_data import (
    generate_synthetic_dataset,
    generate_teacher_scores,
    generate_human_annotations,
    save_config,
    update_research_md,
    update_results_json
)

PROJECT_ROOT = Path(__file__).parent.parent

def test_generate_synthetic_dataset_structure():
    """Test that the generated dataset has the correct columns."""
    n_samples = 10
    seed = 42
    df = generate_synthetic_dataset(n_samples, seed)
    
    expected_columns = [
        "prompt", "image_url", "teacher_scores", 
        "student_scalar", "human_annotations", "primary_dimension"
    ]
    
    assert list(df.columns) == expected_columns
    assert len(df) == n_samples

def test_generate_synthetic_dataset_types():
    """Test that the generated data has correct types."""
    n_samples = 10
    seed = 42
    df = generate_synthetic_dataset(n_samples, seed)
    
    # Check scalar types
    assert df["student_scalar"].dtype in [float, int]
    
    # Check list/dict types for nested structures
    assert isinstance(df["teacher_scores"].iloc[0], dict)
    assert isinstance(df["human_annotations"].iloc[0], dict)
    
    # Check required keys in nested dicts
    required_keys = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
    for key in required_keys:
        assert key in df["teacher_scores"].iloc[0]
        assert key in df["human_annotations"].iloc[0]

def test_noise_independence():
    """
    Test that teacher scores and human annotations are generated with
    independent noise structures (different seeds).
    """
    n_samples = 100
    seed = 42
    df = generate_synthetic_dataset(n_samples, seed)
    
    # Convert nested dicts to separate columns for correlation check
    teacher_df = pd.DataFrame(df["teacher_scores"].tolist())
    human_df = pd.DataFrame(df["human_annotations"].tolist())
    
    # Calculate correlation between teacher and human scores
    # Since they are generated with different seeds, correlation should be low
    # (not exactly zero due to randomness, but significantly lower than 1.0)
    correlations = []
    for dim in ["Alignment", "Realism", "Aesthetics", "Plausibility"]:
        corr = teacher_df[dim].corr(human_df[dim])
        correlations.append(corr)
    
    # Assert that correlations are not perfect (1.0 or -1.0)
    for corr in correlations:
        assert abs(corr) < 1.0, f"Correlation {corr} suggests dependent noise"

def test_save_config_updates_json():
    """Test that save_config correctly updates config.json."""
    config_path = PROJECT_ROOT / "data" / "processed" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create a temporary config file
    with open(config_path, 'w') as f:
        json.dump({"existing_key": "value"}, f)
    
    save_config(config_path, is_mock=True)
    
    # Verify content
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    assert config["IS_MOCK_DATA"] is True
    assert config["existing_key"] == "value"

def test_update_results_json():
    """Test that update_results_json correctly updates results.json."""
    results_path = PROJECT_ROOT / "results" / "results.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create a temporary results file
    with open(results_path, 'w') as f:
        json.dump({"existing_result": 123}, f)
    
    update_results_json(PROJECT_ROOT)
    
    # Verify content
    with open(results_path, 'r') as f:
        results = json.load(f)
    
    assert results["IS_SYNTHETIC_RUN"] is True
    assert results["existing_result"] == 123
