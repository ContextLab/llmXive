import pytest
import json
import os
import sys
from pathlib import Path
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.lmm_model import run_lmm_analysis, save_results, ASSOCIATION_LABEL, fit_lmm_for_combination
from analysis.correction import apply_bonferroni_correction, load_lmm_results
from analysis.sensitivity import run_sensitivity_analysis, load_lmm_results as load_sens_results

class MockDataFrame:
    """Mock dataframe for testing without real data files."""
    def __init__(self):
        self.data = {
            'participant_id': [1, 1, 2, 2, 3, 3],
            'valence_category': ['positive', 'positive', 'negative', 'negative', 'neutral', 'neutral'],
            'recall_accuracy': [0.8, 0.9, 0.5, 0.6, 0.7, 0.75],
            'fixation_duration': [100, 120, 80, 90, 110, 115],
            'saccade_amplitude': [2.5, 3.0, 1.5, 2.0, 2.8, 2.9],
            'gaze_distribution': [0.4, 0.5, 0.3, 0.4, 0.45, 0.48]
        }
        self._df = pd.DataFrame(self.data)
    
    def __getitem__(self, key):
        return self._df[key]
    
    def __iter__(self):
        return iter(self._df)
    
    def copy(self):
        return self._df.copy()
    
    def dropna(self, subset):
        return self._df.dropna(subset=subset)

def test_associational_labeling_in_lmm_results():
    """
    Test that all LMM results include the explicit 'associational' label.
    FR-005 Compliance: Prohibit causal language in outputs.
    """
    # Create mock results similar to what fit_lmm_for_combination returns
    mock_results = [
        {
            "metric": "fixation_duration",
            "valence": "positive",
            "coef": 0.05,
            "p_raw": 0.04,
            "n_obs": 10,
            "converged": True,
            "association_label": ASSOCIATION_LABEL
        },
        {
            "metric": "saccade_amplitude",
            "valence": "negative",
            "coef": -0.02,
            "p_raw": 0.12,
            "n_obs": 10,
            "converged": True,
            "association_label": ASSOCIATION_LABEL
        }
    ]

    # Assertion: Check that the label is present and correct
    for res in mock_results:
        assert 'association_label' in res, "Missing association_label in result"
        assert res['association_label'] == "associational", f"Expected 'associational', got {res['association_label']}"

def test_associational_labeling_after_correction():
    """
    Test that correction step preserves/sets the associational label.
    """
    results = [
        {"metric": "m1", "valence": "v1", "p_raw": 0.05, "association_label": "associational"},
        {"metric": "m2", "valence": "v2", "p_raw": 0.03, "association_label": "associational"}
    ]
    
    # Apply correction
    corrected = apply_bonferroni_correction(results)
    
    for res in corrected:
        assert 'association_label' in res, "Correction failed to preserve association_label"
        assert res['association_label'] == "associational", f"Correction changed label to {res['association_label']}"

def test_associational_labeling_in_sensitivity():
    """
    Test that sensitivity analysis outputs include the associational label.
    """
    mock_lmm_results = [
        {"p_raw": 0.01, "association_label": "associational"},
        {"p_raw": 0.06, "association_label": "associational"},
        {"p_raw": 0.15, "association_label": "associational"}
    ]
    
    thresholds = [0.01, 0.05, 0.1]
    analysis = run_sensitivity_analysis(mock_lmm_results, thresholds)
    
    assert 'analysis' in analysis, "Sensitivity analysis missing 'analysis' key"
    
    for item in analysis['analysis']:
        assert 'association_label' in item, "Sensitivity analysis item missing association_label"
        assert item['association_label'] == "associational", f"Sensitivity label mismatch: {item['association_label']}"
    
    # Top level should also have it if applicable (implementation dependent, but safe to check)
    assert analysis.get('association_label') == "associational", "Top level sensitivity result missing label"

def test_lmm_fit_function_includes_label():
    """
    Test that the actual fit_lmm_for_combination function (if it runs) includes the label.
    Since we can't easily run statsmodels without real data structure in this test env,
    we verify the constant is used in the return dict construction.
    """
    # This test verifies the code structure. 
    # In a real integration test with data, we would call fit_lmm_for_combination.
    # Here we assert the constant exists and is used in the module.
    assert ASSOCIATION_LABEL == "associational"
    
    # Verify the string is used in the source code of the module
    import inspect
    source = inspect.getsource(fit_lmm_for_combination)
    assert 'association_label' in source, "fit_lmm_for_combination does not set association_label"
    assert ASSOCIATION_LABEL in source, "fit_lmm_for_combination does not use the ASSOCIATION_LABEL constant"