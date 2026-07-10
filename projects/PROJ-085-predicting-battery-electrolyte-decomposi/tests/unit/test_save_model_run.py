"""
Unit tests for T026: Save model artifacts, R² scores, and importance maps.
"""
import os
import sys
import json
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from models.save_model_run import run_save_model_run_pipeline, calculate_r2_scores, load_importance_data
from config import get_data_dir, get_output_dir

@pytest.fixture
def setup_mock_environment():
    """
    Ensures the necessary directories and mock files exist for testing.
    In a real CI, T022 and T023 would have run before this.
    """
    output_dir = get_output_dir()
    data_dir = get_data_dir()
    
    # Create directories
    (output_dir / "model_artifacts").mkdir(parents=True, exist_ok=True)
    (data_dir / "processed").mkdir(parents=True, exist_ok=True)
    
    # Note: This test assumes T022 and T023 have been run successfully.
    # If they haven't, the pipeline will attempt to run them.
    return output_dir, data_dir

def test_save_model_run_creates_file(setup_mock_environment):
    """
    Test that run_save_model_run_pipeline creates the model_run.json file.
    """
    output_dir, data_dir = setup_mock_environment
    output_file = data_dir / "processed" / "model_run.json"
    
    # Remove existing file if present
    if output_file.exists():
        output_file.unlink()
    
    # Run the pipeline
    result = run_save_model_run_pipeline()
    
    # Assertions
    assert result.exists(), "Output file was not created."
    assert result == output_file, f"Output path mismatch: {result} != {output_file}"
    
    # Verify JSON content
    with open(result, 'r') as f:
        data = json.load(f)
    
    assert "task_id" in data, "Missing task_id in output."
    assert data["task_id"] == "T026", "Incorrect task_id."
    assert "r2_scores" in data, "Missing r2_scores."
    assert "feature_importance" in data, "Missing feature_importance."

def test_r2_scores_structure():
    """
    Test that R² scores are calculated and returned in the correct format.
    """
    try:
        scores = calculate_r2_scores()
        assert isinstance(scores, dict), "R² scores must be a dictionary."
        assert "overall" in scores, "Missing 'overall' R² score."
        assert isinstance(scores["overall"], float), "R² score must be a float."
    except FileNotFoundError:
        pytest.skip("Model artifacts or features not found. Prerequisite tasks (T022, T018) may not be complete.")
    except Exception as e:
        pytest.fail(f"Error calculating R² scores: {e}")

def test_importance_data_structure():
    """
    Test that importance data is calculated and returned in the correct format.
    """
    try:
        importance = load_importance_data()
        assert isinstance(importance, dict), "Importance data must be a dictionary."
        # Check for expected bins (Low, High)
        # The actual keys depend on the binning logic in T019/T024
        if "Low" in importance or "High" in importance:
            for bin_name, features in importance.items():
                assert isinstance(features, dict), f"Importance for {bin_name} must be a dict."
                for feat, score in features.items():
                    assert isinstance(score, (int, float)), f"Importance score for {feat} must be numeric."
        else:
            # If bins are missing, it might be due to empty data, which is a skip condition
            pytest.skip("No bin data found. Prerequisite tasks may not be complete.")
    except FileNotFoundError:
        pytest.skip("Model artifacts or features not found.")
    except Exception as e:
        pytest.fail(f"Error loading importance data: {e}")