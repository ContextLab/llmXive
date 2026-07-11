"""
Tests for the modeling module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from code.models import fit_linear_mixed_effects

def test_lmm_convergence():
    """Test that LMM converges on simple data."""
    np.random.seed(42)
    n = 100
    data = pd.DataFrame({
        'participant_id': ['P1'] * 50 + ['P2'] * 50,
        'avg_noise_level': np.random.uniform(40, 70, n),
        'noise_variability': np.random.uniform(0, 10, n),
        'reaction_time_mean': np.random.uniform(200, 400, n)
    })

    result = fit_linear_mixed_effects(data)
    assert result['converged'] is True
