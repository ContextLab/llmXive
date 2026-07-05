import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add code directory to path if needed for imports
code_root = Path(__file__).parent.parent.parent / 'code'
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.analysis.modeling import apply_fdr_correction, calculate_correlation_for_metrics

class TestFDRCorrection:
    """Unit tests for FDR correction logic in T026."""

    def test_fdr_correction_basic(self):
        """Test that FDR correction is applied and results are updated."""
        results = [
            {'metric': 'syllable_count', 'r': 0.5, 'p': 0.01},
            {'metric': 'duration', 'r': 0.3, 'p': 0.04},
            {'metric': 'bandwidth', 'r': 0.1, 'p': 0.60},
            {'metric': 'spectral_entropy', 'r': 0.4, 'p': 0.02}
        ]
        
        corrected = apply_fdr_correction(results, alpha=0.05)
        
        assert len(corrected) == 4
        for res in corrected:
            assert 'p_corrected' in res
            assert 'is_significant' in res
            assert isinstance(res['p_corrected'], float)
            assert isinstance(res['is_significant'], bool)

    def test_fdr_correction_significance(self):
        """Test that significant p-values remain significant after correction (usually)."""
        # Create a mix of very small and large p-values
        results = [
            {'metric': 'm1', 'r': 0.8, 'p': 0.0001},
            {'metric': 'm2', 'r': 0.2, 'p': 0.5}
        ]
        
        corrected = apply_fdr_correction(results, alpha=0.05)
        
        # The very small p-value should likely remain significant
        # The large one should not
        m1_sig = [r for r in corrected if r['metric'] == 'm1'][0]
        m2_sig = [r for r in corrected if r['metric'] == 'm2'][0]
        
        assert m1_sig['is_significant'] == True or m1_sig['p_corrected'] < 0.05
        assert m2_sig['is_significant'] == False or m2_sig['p_corrected'] >= 0.05

    def test_fdr_correction_empty_list(self):
        """Test that an empty list returns empty list."""
        results = []
        corrected = apply_fdr_correction(results)
        assert corrected == []

    def test_correlation_metrics_calculation(self):
        """Test that correlation calculation works on mock dataframe."""
        data = {
            'noise_level_db': [30, 40, 50, 60, 70],
            'syllable_count': [10, 12, 15, 18, 20],
            'duration': [1.0, 1.2, 1.5, 1.8, 2.0]
        }
        df = pd.DataFrame(data)
        
        results = calculate_correlation_for_metrics(df)
        
        assert len(results) == 2 # syllable_count and duration
        for res in results:
            assert 'r' in res
            assert 'p' in res
            assert -1 <= res['r'] <= 1
            assert 0 <= res['p'] <= 1