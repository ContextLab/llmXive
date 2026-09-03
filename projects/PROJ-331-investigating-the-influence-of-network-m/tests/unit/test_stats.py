import pytest
import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.multitest import multipletests

# Import functions from the project's stats module
# Note: We assume the module is importable from the code/ directory
# In a real test runner, sys.path would be adjusted or the module installed.
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from stats import load_subject_metrics_data, compute_vif, check_vif_and_select_method, report_insufficient_variance


class TestComputeVIF:
    """Unit tests for compute_vif function."""

    def test_vif_calculation_basic(self):
        """Verify VIF is calculated correctly for a simple case."""
        # Create a simple dataframe with some correlation
        data = {
            'x1': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'x2': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],  # Perfect correlation with x1
            'y': [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
        }
        df = pd.DataFrame(data)
        
        # When x1 and x2 are perfectly correlated, VIF should be very high (or infinite)
        # We expect a large value
        vif_x1 = compute_vif(df, 'x1')
        assert np.isfinite(vif_x1)
        assert vif_x1 > 5.0  # Should be high due to perfect correlation

    def test_vif_no_correlation(self):
        """Verify VIF is low when predictors are uncorrelated."""
        np.random.seed(42)
        data = {
            'x1': np.random.randn(100),
            'x2': np.random.randn(100),
            'y': np.random.randn(100)
        }
        df = pd.DataFrame(data)
        
        vif_x1 = compute_vif(df, 'x1')
        # With random data, VIF should be close to 1
        assert 1.0 <= vif_x1 < 2.0

    def test_vif_single_predictor(self):
        """Verify VIF is 1.0 when there's only one predictor."""
        data = {
            'x1': [1, 2, 3, 4, 5],
            'y': [2, 4, 6, 8, 10]
        }
        df = pd.DataFrame(data)
        
        vif_x1 = compute_vif(df, 'x1')
        assert vif_x1 == 1.0


class TestCheckVifAndSelectMethod:
    """Unit tests for check_vif_and_select_method function."""

    def test_vif_below_threshold_selects_partial(self):
        """Verify that VIF < 5 selects partial correlation method."""
        np.random.seed(42)
        data = {
            'motif_id': ['M1', 'M2', 'M3'],
            'z_score': [1.5, 2.0, 2.5],
            'rsfc_strength': [0.3, 0.4, 0.5],
            'global_node_degree': [10.0, 11.0, 12.0]  # Low variance control
        }
        df = pd.DataFrame(data)
        
        result = check_vif_and_select_method(df, control_var='global_node_degree')
        
        assert result['method_selected'] == 'partial_correlation'
        assert result['vif_value'] < 5.0

    def test_vif_above_threshold_selects_permutation(self):
        """Verify that VIF > 5 selects permutation-only method."""
        # Create data with high correlation between predictor and control
        data = {
            'motif_id': ['M1', 'M2', 'M3', 'M4', 'M5'],
            'z_score': [1.0, 1.1, 1.2, 1.3, 1.4],
            'rsfc_strength': [0.3, 0.4, 0.5, 0.6, 0.7],
            'global_node_degree': [1.0, 1.1, 1.2, 1.3, 1.4]  # Highly correlated with z_score
        }
        df = pd.DataFrame(data)
        
        result = check_vif_and_select_method(df, control_var='global_node_degree')
        
        assert result['method_selected'] == 'permutation_only'
        assert result['vif_value'] >= 5.0

    def test_zero_variance_detection(self):
        """Verify zero variance in z_scores is detected."""
        data = {
            'motif_id': ['M1', 'M2', 'M3'],
            'z_score': [2.0, 2.0, 2.0],  # Zero variance
            'rsfc_strength': [0.3, 0.4, 0.5],
            'global_node_degree': [10.0, 11.0, 12.0]
        }
        df = pd.DataFrame(data)
        
        result = check_vif_and_select_method(df, control_var='global_node_degree')
        
        assert result['zero_variance'] is True
        # Should still select a method, likely permutation due to zero variance
        assert result['method_selected'] in ['partial_correlation', 'permutation_only']


class TestReportInsufficientVariance:
    """Unit tests for report_insufficient_variance function."""

    def test_returns_correct_message(self):
        """Verify the function returns the correct message format."""
        motif_id = "M13"
        result = report_insufficient_variance(motif_id)
        
        assert isinstance(result, dict)
        assert 'motif_id' in result
        assert result['motif_id'] == motif_id
        assert 'status' in result
        assert result['status'] == 'insufficient_variance'
        assert 'message' in result
        assert 'insufficient variance' in result['message'].lower()

    def test_handles_different_motif_ids(self):
        """Verify the function works with different motif IDs."""
        for motif_id in ['M1', 'M13', 'M256']:
            result = report_insufficient_variance(motif_id)
            assert result['motif_id'] == motif_id
            assert result['status'] == 'insufficient_variance'


class TestLoadSubjectMetricsData:
    """Unit tests for load_subject_metrics_data function."""

    def test_loads_from_csv(self):
        """Verify the function loads data from a CSV file."""
        import tempfile
        import os
        
        # Create a temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("subject_id,motif_id,z_score,rsfc_strength,global_node_degree\n")
            f.write("sub-001,M1,1.5,0.3,10.0\n")
            f.write("sub-002,M1,1.6,0.4,11.0\n")
            temp_path = f.name
        
        try:
            df = load_subject_metrics_data(temp_path)
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 2
            assert 'subject_id' in df.columns
            assert 'motif_id' in df.columns
        finally:
            os.unlink(temp_path)

    def test_handles_missing_file(self):
        """Verify the function raises an error for missing files."""
        with pytest.raises(FileNotFoundError):
            load_subject_metrics_data("nonexistent_file.csv")


class TestBonferroniCorrection:
    """Unit tests for Bonferroni correction logic (using statsmodels)."""

    def test_bonferroni_corrects_p_values(self):
        """Verify Bonferroni correction increases p-values."""
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05]
        corrected = multipletests(p_values, method='bonferroni')[1]
        
        # Corrected p-values should be >= original p-values
        assert all(corrected >= p_values)
        
        # Corrected p-values should be <= 1.0
        assert all(corrected <= 1.0)
        
        # The smallest corrected p-value should be approximately min(p) * n
        expected_min = min(p_values) * len(p_values)
        assert abs(corrected[0] - expected_min) < 0.001

    def test_bonferroni_with_many_tests(self):
        """Verify Bonferroni correction with a larger number of tests."""
        np.random.seed(42)
        p_values = np.random.uniform(0, 1, 13)  # 13 motifs
        corrected = multipletests(p_values, method='bonferroni')[1]
        
        # All corrected values should be <= 1.0
        assert all(corrected <= 1.0)
        
        # The number of corrected values should match the input
        assert len(corrected) == len(p_values)

    def test_bonferroni_with_zero_p_value(self):
        """Verify Bonferroni handles zero p-values."""
        p_values = [0.0, 0.01, 0.02]
        corrected = multipletests(p_values, method='bonferroni')[1]
        
        # Zero p-value should remain zero (or very close to it)
        assert corrected[0] == 0.0 or corrected[0] < 1e-10
        # Other values should be corrected
        assert corrected[1] > 0.01
        assert corrected[2] > 0.02
