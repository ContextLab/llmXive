import pytest
import pandas as pd
import numpy as np
from code.analysis import classify_early_ad_dynamic
from code.config import set_seed

class TestDynamicEarlyADClassification:
    """
    Unit tests for T022: Dynamic 'Early AD' classification based on amyloid-beta threshold.
    
    Tests the logic defined in T024:
    1. If labels exist, use them.
    2. If amyloid_beta_load exists, calculate upper quantile of 'Normal' group.
    3. If amyloid_beta_load missing, fallback to tau_markers.
    4. Verify classification logic and logging.
    """

    def test_uses_existing_labels(self):
        """Test that if 'pathology_status' is already populated, it is respected."""
        set_seed(42)
        data = pd.DataFrame({
            'subject_id': [1, 2, 3],
            'brain_region': ['Hippocampus', 'Prefrontal Cortex', 'Hippocampus'],
            'pathology_status': ['Normal', 'Early AD', 'Normal'],
            'amyloid_beta_load': [0.5, 2.0, 0.6],
            'cognitive_score': [1.0, 0.2, 0.9]
        })

        result = classify_early_ad_dynamic(data)

        # Should remain unchanged
        assert result['pathology_status'].tolist() == ['Normal', 'Early AD', 'Normal']

    def test_classifies_based_on_amyloid_threshold(self):
        """Test classification when amyloid_beta_load is present and labels are missing."""
        set_seed(42)
        # Create data where 'Normal' group has low amyloid, and one subject has high amyloid
        # Threshold should be calculated as the upper quantile (e.g., 90th or 95th) of the 'Normal' group
        data = pd.DataFrame({
            'subject_id': [1, 2, 3, 4],
            'brain_region': ['Hippocampus', 'Hippocampus', 'Hippocampus', 'Hippocampus'],
            'pathology_status': ['Normal', 'Normal', 'Normal', None], # One missing label
            'amyloid_beta_load': [0.1, 0.2, 0.15, 0.9], # 0.9 is high compared to 0.1-0.2
            'cognitive_score': [1.0, 0.9, 0.95, 0.3]
        })

        result = classify_early_ad_dynamic(data)

        # The subject with 0.9 amyloid load should be classified as 'Early AD'
        # The others should remain 'Normal'
        assert result.loc[3, 'pathology_status'] == 'Early AD'
        assert result.loc[0, 'pathology_status'] == 'Normal'
        assert result.loc[1, 'pathology_status'] == 'Normal'
        assert result.loc[2, 'pathology_status'] == 'Normal'

    def test_fallback_to_tau_markers(self):
        """Test fallback logic when amyloid_beta_load is missing but tau_markers is present."""
        set_seed(42)
        data = pd.DataFrame({
            'subject_id': [1, 2, 3, 4],
            'brain_region': ['Hippocampus', 'Hippocampus', 'Hippocampus', 'Hippocampus'],
            'pathology_status': ['Normal', 'Normal', 'Normal', None],
            'amyloid_beta_load': [None, None, None, None], # Missing
            'tau_markers': [1.0, 1.2, 1.1, 5.0], # 5.0 is high
            'cognitive_score': [1.0, 0.9, 0.95, 0.3]
        })

        result = classify_early_ad_dynamic(data)

        # The subject with 5.0 tau should be classified as 'Early AD'
        assert result.loc[3, 'pathology_status'] == 'Early AD'
        assert result.loc[0, 'pathology_status'] == 'Normal'

    def test_raises_error_if_no_markers(self):
        """Test that an error is raised if neither amyloid nor tau markers are available."""
        set_seed(42)
        data = pd.DataFrame({
            'subject_id': [1, 2],
            'brain_region': ['Hippocampus', 'Hippocampus'],
            'pathology_status': [None, None],
            'amyloid_beta_load': [None, None],
            'tau_markers': [None, None],
            'cognitive_score': [1.0, 0.9]
        })

        with pytest.raises(ValueError, match="No pathology markers found"):
            classify_early_ad_dynamic(data)

    def test_quantile_calculation_logic(self):
        """Verify the specific quantile threshold calculation logic."""
        set_seed(42)
        # Control group: [10, 10, 10, 10, 10] -> 90th percentile is 10
        # Test subject: 11 -> should be Early AD
        data = pd.DataFrame({
            'subject_id': list(range(7)),
            'brain_region': ['Hippocampus'] * 7,
            'pathology_status': ['Normal'] * 5 + [None, None],
            'amyloid_beta_load': [10.0, 10.0, 10.0, 10.0, 10.0, 11.0, 9.0],
            'cognitive_score': [1.0] * 7
        })

        result = classify_early_ad_dynamic(data)

        # Subject 5 (11.0) > threshold (10.0) -> Early AD
        assert result.loc[5, 'pathology_status'] == 'Early AD'
        # Subject 6 (9.0) < threshold -> Normal
        assert result.loc[6, 'pathology_status'] == 'Normal'