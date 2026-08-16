import pytest
import numpy as np
import sys
import os

# Add the parent directory to the path to allow imports from code/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.metrics import MetricCalculator
from code.models import DefectGraph
import networkx as nx

class TestBonferroniVerification:
    """
    Tests for the Bonferroni correction verification logic in MetricCalculator.
    Directly addresses FR-006 requirements.
    """

    def setup_method(self):
        """Setup test fixtures."""
        self.calculator = MetricCalculator()
        # Create a dummy graph for the DefectGraph object
        G = nx.erdos_renyi_graph(10, 0.3)
        self.graph_obj = DefectGraph(graph=G)

    def test_no_flags_when_all_pass(self):
        """
        Test case where all p-values remain significant after correction.
        Expected: No flags.
        """
        # Small p-values that survive a Bonferroni correction for 5 tests
        # alpha = 0.05, corrected_threshold = 0.01
        # All p < 0.005
        raw_p_values = [0.001, 0.002, 0.003, 0.004, 0.005]
        
        result = self.calculator._verify_bonferroni_correction(raw_p_values)
        
        assert result['n_tests'] == 5
        assert result['alpha'] == 0.05
        assert result['corrected_threshold'] == 0.01
        assert len(result['flags']) == 0
        assert 'No metrics lost significance' in result['summary']

    def test_flags_when_some_fail(self):
        """
        Test case where some p-values are significant uncorrected but not corrected.
        Expected: Flags raised for these specific indices.
        """
        # alpha = 0.05, n=5 -> corrected_threshold = 0.01
        # p[0] = 0.005 (sig both)
        # p[1] = 0.02 (sig uncorrected, NOT sig corrected) -> SHOULD FLAG
        # p[2] = 0.08 (not sig uncorrected)
        # p[3] = 0.009 (sig both)
        # p[4] = 0.015 (sig uncorrected, NOT sig corrected) -> SHOULD FLAG
        raw_p_values = [0.005, 0.02, 0.08, 0.009, 0.015]
        
        result = self.calculator._verify_bonferroni_correction(raw_p_values)
        
        assert result['n_tests'] == 5
        assert result['corrected_threshold'] == 0.01
        assert len(result['flags']) == 2
        
        # Check specific indices flagged
        flagged_indices = [f['index'] for f in result['flags']]
        assert 1 in flagged_indices
        assert 4 in flagged_indices
        
        # Verify reason string
        for flag in result['flags']:
            assert 'Significant uncorrected, non-significant corrected' in flag['reason']

    def test_empty_list(self):
        """Test handling of empty p-value list."""
        raw_p_values = []
        result = self.calculator._verify_bonferroni_correction(raw_p_values)
        
        assert result['n_tests'] == 0
        assert np.isnan(result['corrected_threshold'])
        assert len(result['flags']) == 0
        assert 'No p-values provided' in result['summary']

    def test_integration_with_defect_graph(self):
        """
        Test that the verification is correctly integrated into calculate_all
        when metadata is present.
        """
        raw_p_values = [0.04, 0.001] # 0.04 < 0.05 but > 0.025 (0.05/2) -> Flag
        self.graph_obj.metadata = {'raw_p_values': raw_p_values}
        
        metrics = self.calculator.calculate_all(self.graph_obj)
        
        assert 'bonferroni_verification' in metrics
        assert metrics['bonferroni_verification'] is not None
        assert len(metrics['bonferroni_verification']['flags']) == 1
        assert metrics['bonferroni_verification']['flags'][0]['index'] == 0

    def test_integration_without_metadata(self):
        """
        Test that calculate_all handles missing metadata gracefully.
        """
        # Ensure metadata is None or empty
        self.graph_obj.metadata = None
        
        metrics = self.calculator.calculate_all(self.graph_obj)
        
        assert 'bonferroni_verification' in metrics
        assert metrics['bonferroni_verification'] is None

    def test_single_test(self):
        """
        Test with a single p-value.
        Corrected threshold should equal alpha (0.05/1).
        """
        raw_p_values = [0.03]
        result = self.calculator._verify_bonferroni_correction(raw_p_values)
        
        assert result['n_tests'] == 1
        assert result['corrected_threshold'] == 0.05
        assert len(result['flags']) == 0 # 0.03 < 0.05, so it stays significant
        
        # Test case where it fails
        raw_p_values_fail = [0.06]
        result_fail = self.calculator._verify_bonferroni_correction(raw_p_values_fail)
        assert len(result_fail['flags']) == 0 # 0.06 > 0.05, so never significant uncorrected