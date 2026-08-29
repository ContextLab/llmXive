import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from robustness_sweep import calculate_belief_stats

class TestCalculateBeliefStats:
    def test_calculate_belief_stats(self):
        df = pd.DataFrame({
            'belief_rating': [1, 2, 3, 4, 5]
        })
        
        stats = calculate_belief_stats(df, 'belief_rating')
        
        assert stats['mean'] == 3.0
        assert stats['std'] == pytest.approx(1.58, rel=0.01)
        assert stats['min'] == 1.0
        assert stats['max'] == 5.0
        assert stats['range'] == 4.0

    def test_calculate_belief_stats_empty(self):
        df = pd.DataFrame({'belief_rating': []})
        
        stats = calculate_belief_stats(df, 'belief_rating')
        
        assert np.isnan(stats['mean'])
        assert np.isnan(stats['std'])
