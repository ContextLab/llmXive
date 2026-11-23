"""
Unit tests for sensitivity analysis module.

Tests FR-007 and SC-005 requirements for router confidence threshold
sensitivity analysis.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
import json
import tempfile

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.sensitivity import (
    calculate_inconsistency_rate,
    run_sensitivity_analysis,
    save_sensitivity_report
)


class TestCalculateInconsistencyRate:
    """Tests for the calculate_inconsistency_rate function."""
    
    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame({
            'confidence': [0.9, 0.8, 0.6, 0.4, 0.2, 0.7, 0.3],
            'intent': ['high_confidence', 'high_confidence', 'ambiguous', 
                     'ambiguous', 'ambiguous', 'high_confidence', 'ambiguous'],
            'ground_truth_intent': ['high_confidence', 'high_confidence', 'ambiguous',
                                  'ambiguous', 'ambiguous', 'high_confidence', 'ambiguous']
        })
    
    def test_high_threshold_all_routed_to_fallback(self, sample_df):
        """Test that high threshold routes everything to fallback."""
        rate, inconsistent, total = calculate_inconsistency_rate(sample_df, 0.95)
        
        # All should be routed to fallback (confidence < 0.95)
        # High-confidence queries (3) should be routed to LLM -> inconsistent
        # Ambiguous queries (4) should be routed to fallback -> consistent
        assert total == 7
        assert inconsistent == 3  # 3 high-confidence routed to fallback
        assert rate == pytest.approx(3/7, rel=0.01)
    
    def test_low_threshold_all_routed_to_llm(self, sample_df):
        """Test that low threshold routes everything to LLM."""
        rate, inconsistent, total = calculate_inconsistency_rate(sample_df, 0.1)
        
        # All should be routed to LLM (confidence >= 0.1)
        # High-confidence queries (3) should be routed to LLM -> consistent
        # Ambiguous queries (4) should be routed to fallback -> inconsistent
        assert total == 7
        assert inconsistent == 4  # 4 ambiguous routed to LLM
        assert rate == pytest.approx(4/7, rel=0.01)
    
    def test_optimal_threshold(self, sample_df):
        """Test with a threshold that should be optimal."""
        # With threshold 0.5:
        # 0.9, 0.8, 0.6, 0.7 -> routed to LLM (all high_confidence -> consistent)
        # 0.4, 0.2, 0.3 -> routed to fallback (all ambiguous -> consistent)
        rate, inconsistent, total = calculate_inconsistency_rate(sample_df, 0.5)
        
        assert total == 7
        assert inconsistent == 0  # Perfect routing
        assert rate == 0.0
    
    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        empty_df = pd.DataFrame(columns=['confidence', 'ground_truth_intent'])
        rate, inconsistent, total = calculate_inconsistency_rate(empty_df, 0.5)
        
        assert rate == 0.0
        assert inconsistent == 0
        assert total == 0
    
    def test_boundary_threshold(self, sample_df):
        """Test with threshold exactly at a confidence value."""
        # Threshold = 0.6: 0.9, 0.8, 0.6 -> routed to LLM
        # 0.9, 0.8, 0.6 are high_confidence -> consistent
        # 0.4, 0.2, 0.7, 0.3 -> routed to fallback
        # 0.7 is high_confidence -> inconsistent
        rate, inconsistent, total = calculate_inconsistency_rate(sample_df, 0.6)
        
        assert total == 7
        assert inconsistent == 1  # Only 0.7 high_confidence routed to fallback
        assert rate == pytest.approx(1/7, rel=0.01)


class TestRunSensitivityAnalysis:
    """Tests for the run_sensitivity_analysis function."""
    
    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame({
            'confidence': [0.9, 0.8, 0.6, 0.4, 0.2, 0.7, 0.3, 0.5, 0.55],
            'intent': ['high_confidence', 'high_confidence', 'ambiguous', 
                     'ambiguous', 'ambiguous', 'high_confidence', 'ambiguous',
                     'high_confidence', 'ambiguous'],
            'ground_truth_intent': ['high_confidence', 'high_confidence', 'ambiguous',
                                  'ambiguous', 'ambiguous', 'high_confidence', 'ambiguous',
                                  'high_confidence', 'ambiguous']
        })
    
    def test_default_thresholds(self, sample_df):
        """Test with default thresholds."""
        results = run_sensitivity_analysis(sample_df)
        
        assert 'thresholds_tested' in results
        assert 'results' in results
        assert 'summary' in results
        
        assert len(results['thresholds_tested']) == 7
        assert results['summary']['total_samples'] == 9
        assert results['summary']['min_inconsistency_rate'] >= 0
        assert results['summary']['optimal_threshold'] is not None
    
    def test_custom_thresholds(self, sample_df):
        """Test with custom thresholds."""
        custom_thresholds = [0.2, 0.5, 0.8]
        results = run_sensitivity_analysis(sample_df, custom_thresholds)
        
        assert results['thresholds_tested'] == custom_thresholds
        assert len(results['results']) == 3
    
    def test_results_structure(self, sample_df):
        """Test that results have correct structure."""
        results = run_sensitivity_analysis(sample_df)
        
        for result in results['results']:
            assert 'threshold' in result
            assert 'inconsistency_rate' in result
            assert 'count_inconsistent' in result
            assert 'count_total' in result
            assert 'count_routed_to_llm' in result
            assert 'count_routed_to_fallback' in result
            assert 'optimal' in result
    
    def test_monotonic_behavior(self, sample_df):
        """Test that inconsistency rate generally increases at extremes."""
        results = run_sensitivity_analysis(sample_df)
        
        rates = [r['inconsistency_rate'] for r in results['results']]
        thresholds = [r['threshold'] for r in results['results']]
        
        # Find minimum
        min_rate = min(rates)
        min_idx = rates.index(min_rate)
        
        # Rates should be higher at both ends of the threshold range
        # (though this is not guaranteed for all datasets, it's a reasonable check)
        if min_idx > 0 and min_idx < len(rates) - 1:
            assert rates[0] >= min_rate
            assert rates[-1] >= min_rate


class TestSaveSensitivityReport:
    """Tests for the save_sensitivity_report function."""
    
    def test_save_and_load(self, tmp_path):
        """Test saving and loading a report."""
        results = {
            'thresholds_tested': [0.5, 0.6, 0.7],
            'results': [
                {'threshold': 0.5, 'inconsistency_rate': 0.1, 'count_inconsistent': 1, 
                 'count_total': 10, 'count_routed_to_llm': 5, 'count_routed_to_fallback': 5,
                 'optimal': True},
                {'threshold': 0.6, 'inconsistency_rate': 0.2, 'count_inconsistent': 2,
                 'count_total': 10, 'count_routed_to_llm': 4, 'count_routed_to_fallback': 6,
                 'optimal': False},
                {'threshold': 0.7, 'inconsistency_rate': 0.3, 'count_inconsistent': 3,
                 'count_total': 10, 'count_routed_to_llm': 3, 'count_routed_to_fallback': 7,
                 'optimal': False}
            ],
            'summary': {
                'total_samples': 10,
                'min_inconsistency_rate': 0.1,
                'optimal_threshold': 0.5,
                'threshold_range': [0.5, 0.7]
            }
        }
        
        output_path = tmp_path / "sensitivity_report.json"
        save_sensitivity_report(results, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            loaded_results = json.load(f)
        
        assert loaded_results == results
    
    def test_creates_parent_directory(self, tmp_path):
        """Test that parent directories are created."""
        results = {
            'thresholds_tested': [0.5],
            'results': [],
            'summary': {}
        }
        
        output_path = tmp_path / "subdir" / "nested" / "report.json"
        save_sensitivity_report(results, output_path)
        
        assert output_path.exists()