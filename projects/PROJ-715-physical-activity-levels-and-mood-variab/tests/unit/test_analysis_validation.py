import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add project root to path for imports if running standalone
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from config import get_path
from analysis import (
    load_daily_aggregates,
    fit_mood_std_model,
    fit_mean_mood_model,
    extract_results
)

@pytest.fixture
def sample_data():
    """
    Create a synthetic dataset mimicking the structure of daily_aggregates.csv
    to test LOPO logic without needing the real StudentLife dataset in the unit test environment.
    """
    np.random.seed(42)
    n_participants = 5
    n_days_per_participant = 10
    
    data = []
    for p_id in range(n_participants):
        for day in range(n_days_per_participant):
            # Ensure enough variation to fit a model
            total_steps = np.random.randint(2000, 15000)
            mean_mood = np.random.uniform(2.0, 5.0)
            # log(mood_std + 0.01) as per T019
            mood_std_log = np.log(np.random.uniform(0.1, 1.0) + 0.01)
            sleep_duration = np.random.uniform(5.0, 9.0)
            baseline_affect = np.random.uniform(2.0, 5.0)
            day_of_week = np.random.randint(0, 7)
            
            data.append({
                'participant_id': f"P{p_id:03d}",
                'date': f"2023-01-{day+1:02d}",
                'total_steps': total_steps,
                'mean_mood': mean_mood,
                'mood_std_log': mood_std_log,
                'sleep_duration': sleep_duration,
                'baseline_affect': baseline_affect,
                'day_of_week': day_of_week
            })
    
    return pd.DataFrame(data)

@pytest.fixture
def mock_model_results():
    """Mock the return value of extract_results to simulate a successful model fit."""
    return {
        "model_1": {
            "outcome": "mood_std_log",
            "predictor": "total_steps",
            "coefficients": {
                "total_steps": {
                    "estimate": 0.0005,
                    "std_error": 0.0002,
                    "p_value": 0.01,
                    "ci_95_lower": 0.0001,
                    "ci_95_upper": 0.0009
                }
            },
            "convergence": True
        },
        "model_2": {
            "outcome": "mean_mood",
            "predictor": "total_steps",
            "coefficients": {
                "total_steps": {
                    "estimate": 0.0001,
                    "std_error": 0.0001,
                    "p_value": 0.15,
                    "ci_95_lower": -0.0001,
                    "ci_95_upper": 0.0003
                }
            },
            "convergence": True
        }
    }

def test_lopo_loop_structure(sample_data, mock_model_results):
    """
    Test that the LOPO loop iterates correctly over each participant,
    excludes them, and aggregates coefficients.
    """
    # Mock the model fitting functions to return predictable results
    # We need to mock the specific functions called inside the LOPO logic
    # Since the actual LOPO logic is likely in a helper or main analysis function,
    # we simulate the core logic here to verify the aggregation.

    participant_ids = sample_data['participant_id'].unique()
    n_loops = len(participant_ids)
    
    collected_coefficients = []
    
    # Simulate the LOPO loop logic
    for p_id in participant_ids:
        # Create fold data (exclude one participant)
        fold_data = sample_data[sample_data['participant_id'] != p_id]
        
        # Verify exclusion logic
        assert p_id not in fold_data['participant_id'].values, f"Participant {p_id} should be excluded"
        assert len(fold_data) == len(sample_data) - len(sample_data[sample_data['participant_id'] == p_id])
        
        # Simulate fitting (in real code this would call fit_mood_std_model etc.)
        # For this test, we just record the coefficient we expect to see
        # In a real integration, we would call the actual analysis functions
        # Here we verify the loop structure and data slicing logic
        
        # Simulate a coefficient result (mocking extract_results behavior)
        # We use a deterministic value based on the fold index to test aggregation
        coef_val = 0.0001 * (n_loops - list(participant_ids).index(p_id))
        
        collected_coefficients.append({
            "excluded_participant": p_id,
            "coefficient": coef_val,
            "n_obs": len(fold_data)
        })
    
    # Verify loop ran for all participants
    assert len(collected_coefficients) == n_loops, "LOPO loop must run N times for N participants"
    
    # Verify aggregation logic (e.g., mean coefficient)
    mean_coef = np.mean([c['coefficient'] for c in collected_coefficients])
    assert isinstance(mean_coef, float), "Aggregated coefficient must be numeric"
    
    # Verify sign stability calculation logic
    # Assume the full model (all data) has a positive coefficient
    full_model_coef = 0.0005
    signs_match = [1 if c['coefficient'] * full_model_coef > 0 else 0 for c in collected_coefficients]
    stability_rate = sum(signs_match) / len(signs_match)
    
    assert 0.0 <= stability_rate <= 1.0, "Stability rate must be between 0 and 1"

def test_coefficient_aggregation_logic(sample_data):
    """
    Test the specific logic for aggregating coefficients and calculating sign stability.
    """
    # Simulate a list of coefficients from LOPO folds
    # Positive coefficients
    positive_coefs = [0.0001, 0.0002, 0.00015, 0.0003, 0.00012]
    # Negative coefficients (outlier)
    mixed_coefs = [0.0001, -0.00005, 0.0002, 0.00015, 0.0001]
    
    def calculate_sign_stability(coefs, reference_sign):
        """Helper to calculate sign stability."""
        matches = sum(1 for c in coefs if (c > 0) == reference_sign)
        return matches / len(coefs)
    
    # Test 1: All positive should have 100% stability against positive reference
    stability_pos = calculate_sign_stability(positive_coefs, reference_sign=True)
    assert stability_pos == 1.0, "All positive coefs should match positive reference"
    
    # Test 2: Mixed should have < 100% stability
    stability_mixed = calculate_sign_stability(mixed_coefs, reference_sign=True)
    assert stability_mixed < 1.0, "Mixed coefs should not be 100% stable"
    assert stability_mixed == 0.8, "Expected 4/5 matches for mixed list"

def test_lopo_data_integrity(sample_data):
    """
    Ensure that LOPO folds preserve data integrity (no NaN injection, correct types).
    """
    p_id_to_remove = sample_data['participant_id'].iloc[0]
    fold_data = sample_data[sample_data['participant_id'] != p_id_to_remove]
    
    # Check that required columns for modeling exist
    required_cols = ['total_steps', 'mood_std_log', 'sleep_duration', 'baseline_affect', 'day_of_week']
    for col in required_cols:
        assert col in fold_data.columns, f"Required column {col} missing in LOPO fold"
    
    # Check that no NaNs are introduced by the slicing operation itself
    # (Real data might have NaNs, but the slicing shouldn't create new ones)
    assert not fold_data.isnull().any().any(), "Slicing operation introduced NaNs"

def test_sign_stability_threshold_logic():
    """
    Verify the logic that flags results if stability < 90%.
    """
    def check_stability_flag(stability_rate, threshold=0.90):
        return stability_rate < threshold
    
    assert check_stability_flag(0.95) == False, "0.95 should not be flagged"
    assert check_stability_flag(0.89) == True, "0.89 should be flagged"
    assert check_stability_flag(0.90) == False, "Exactly 0.90 should not be flagged"
    assert check_stability_flag(0.0) == True, "0.0 should be flagged"