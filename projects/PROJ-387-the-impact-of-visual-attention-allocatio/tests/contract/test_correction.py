import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from analysis.correction import apply_bonferroni_correction

class TestBonferroniCorrection:
    
    def test_correction_calculation(self):
        """Test that Bonferroni correction multiplies p-value by 9."""
        test_data = [
            {"metric": "fixation", "valence": "positive", "p_raw": 0.01},
            {"metric": "saccade", "valence": "neutral", "p_raw": 0.05},
            {"metric": "gaze", "valence": "negative", "p_raw": 0.20}
        ]
        
        results = apply_bonferroni_correction(test_data)
        
        assert len(results) == 3
        
        # Check first: 0.01 * 9 = 0.09
        assert abs(results[0]['p_corrected'] - 0.09) < 1e-6
        assert results[0]['association_label'] == "associational"
        
        # Check second: 0.05 * 9 = 0.45
        assert abs(results[1]['p_corrected'] - 0.45) < 1e-6
        
        # Check third: 0.20 * 9 = 1.8 -> capped at 1.0
        assert results[2]['p_corrected'] == 1.0

    def test_empty_list(self):
        """Test handling of empty input list."""
        results = apply_bonferroni_correction([])
        assert results == []

    def test_metadata_preservation(self):
        """Test that original metadata is preserved in the result."""
        test_data = [
            {"metric": "fixation", "valence": "positive", "coef": 0.5, "p_raw": 0.01}
        ]
        
        results = apply_bonferroni_correction(test_data)
        
        assert results[0]['metric'] == "fixation"
        assert results[0]['valence'] == "positive"
        assert results[0]['coef'] == 0.5
        assert 'p_corrected' in results[0]
        assert 'n_comparisons' in results[0]
        assert results[0]['n_comparisons'] == 9