"""
Unit tests for the analysis module (T021).

Tests:
- Schema validation of output
- Model fitting logic (mocked)
- MDE calculation logic
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis import (
    fit_lmm,
    calculate_mde,
    run_multiple_comparison_correction,
    write_results
)
from config import set_seed

@pytest.fixture
def mock_df():
    """Create a mock dataframe for testing."""
    np.random.seed(42)
    n = 100
    return pd.DataFrame({
        'duration_estimate': np.random.normal(10, 2, n),
        'surprisal': np.random.normal(0, 1, n),
        'sequence_length': np.random.randint(1, 10, n),
        'modality': np.random.choice(['visual', 'auditory'], n),
        'participant_id': np.random.choice([f'P{i}' for i in range(10)], n)
    })

@pytest.fixture
def results_dir(tmp_path):
    """Create a temporary directory for results."""
    (tmp_path / "analysis").mkdir()
    return tmp_path

def test_fit_lmm_basic(mock_df):
    """Test that LMM fitting returns a valid summary structure."""
    formula = "duration_estimate ~ surprisal + sequence_length + C(modality) + (1 | participant_id)"
    
    # Mock the statsmodels fitting to avoid heavy computation in unit tests
    # In a real integration test, we would run the actual fit.
    # Here we verify the logic flow.
    with patch('statsmodels.formula.api.mixedlm') as mock_mixedlm:
        mock_result = MagicMock()
        mock_result.converged = True
        mock_result.params = {
            'surprisal': 0.5,
            'sequence_length': 0.1,
            'C(modality)[T.auditory]': 1.2,
            'Group Var': 0.5
        }
        mock_result.bse = {
            'surprisal': 0.1,
            'sequence_length': 0.05,
            'C(modality)[T.auditory]': 0.2,
            'Group Var': 0.1
        }
        mock_result.pvalues = {
            'surprisal': 0.001,
            'sequence_length': 0.05,
            'C(modality)[T.auditory]': 0.0001,
            'Group Var': 0.1
        }
        mock_result.conf_int.return_value = pd.DataFrame({
            0: [0.3, 0.0, 0.8, 0.3],
            1: [0.7, 0.2, 1.6, 0.7]
        }, index=['surprisal', 'sequence_length', 'C(modality)[T.auditory]', 'Group Var'])
        
        mock_mixedlm.return_value.fit.return_value = mock_result
        
        model, summary = fit_lmm(mock_df, formula)
        
        assert model is not None
        assert "fixed_effects" in summary
        assert "surprisal" in summary["fixed_effects"]
        assert "coef" in summary["fixed_effects"]["surprisal"]
        assert "pval" in summary["fixed_effects"]["surprisal"]
        assert "ci_95" in summary["fixed_effects"]["surprisal"]

def test_multiple_comparison_correction():
    """Test that p-values are corrected."""
    summary = {
        "fixed_effects": {
            "effect1": {"pval": 0.01},
            "effect2": {"pval": 0.04},
            "effect3": {"pval": 0.06}
        }
    }
    
    corrected = run_multiple_comparison_correction(summary)
    
    assert "correction_method" in corrected
    assert corrected["correction_method"] == "fdr_bh"
    assert "pval_corrected" in corrected["fixed_effects"]["effect1"]

def test_mde_calculation(mock_df):
    """Test MDE calculation logic."""
    summary = {
        "fixed_effects": {"surprisal": {"coef": 0.5}},
        "converged": True
    }
    
    mde_info = calculate_mde(mock_df, summary)
    
    assert "mde" in mde_info
    assert "power" in mde_info
    assert mde_info["power"] == 0.80
    assert mde_info["mde"] > 0

def test_write_results(results_dir):
    """Test that results are written to JSON correctly."""
    test_data = {
        "status": "completed",
        "task": "T021",
        "fixed_effects": {"test": 1.0}
    }
    
    # Temporarily change working directory for the test
    original_cwd = os.getcwd()
    os.chdir(results_dir)
    
    try:
        write_results(test_data)
        
        output_path = results_dir / "analysis" / "results.json"
        assert output_path.exists()
        
        with open(output_path) as f:
            loaded = json.load(f)
        
        assert loaded["status"] == "completed"
    finally:
        os.chdir(original_cwd)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
