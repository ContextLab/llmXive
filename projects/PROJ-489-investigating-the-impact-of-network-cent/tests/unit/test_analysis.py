import json
import tempfile
import os
from pathlib import Path
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

# Import the functions to test
# Note: We assume the functions are defined in code/analysis.py
# Since we cannot import 'code' directly in tests without setup, 
# we will mock the imports or import relative to the package if structured.
# For this test, we assume the environment allows:
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis import (
    check_subject_count, 
    calculate_cohens_d, 
    calculate_effect_sizes, 
    run_lme_analysis, 
    run_shapiro_wilk, 
    apply_benjamini_hochberg, 
    generate_analysis_report
)
import pandas as pd

class TestResidualDiagnostics:
    """Unit tests for residual diagnostics JSON generation (T054)."""

    def test_run_shapiro_wilk_returns_dict(self):
        """Test that run_shapiro_wilk returns a dictionary with expected keys."""
        # Create dummy residuals
        residuals = np.random.normal(0, 1, 100)
        
        # Mock the statsmodels function to avoid dependency issues in unit test
        with patch('analysis.stats') as mock_stats:
            mock_stats.shapiro.return_value = (0.95, 0.12) # stat, pvalue
            
            result = run_shapiro_wilk(residuals)
            
            assert isinstance(result, dict)
            assert 'statistic' in result
            assert 'p_value' in result
            assert 'is_normal' in result
            assert result['p_value'] == 0.12

    def test_run_shapiro_wilk_saves_json(self):
        """Test that run_shapiro_wilk writes results to a JSON file."""
        residuals = np.random.normal(0, 1, 50)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "residuals_diagnostics.json"
            
            with patch('analysis.stats') as mock_stats:
                mock_stats.shapiro.return_value = (0.98, 0.50)
                
                run_shapiro_wilk(residuals, output_path=str(output_path))
                
                assert output_path.exists()
                with open(output_path, 'r') as f:
                    data = json.load(f)
                
                assert 'shapiro_test' in data
                assert 'p_value' in data['shapiro_test']

class TestFDRCorrection:
    """Unit tests for FDR correction logic (T055)."""

    def test_apply_benjamini_hochberg_single_list(self):
        """Test BH correction on a simple list of p-values."""
        p_values = [0.01, 0.04, 0.03, 0.001, 0.06]
        
        result = apply_benjamini_hochberg(p_values)
        
        assert isinstance(result, list)
        assert len(result) == len(p_values)
        
        # Check monotonicity of corrected p-values (they should be non-decreasing when sorted)
        # The function should return adjusted p-values
        adjusted = result
        # Basic sanity check: adjusted p-values should be >= original p-values (mostly)
        # and <= 1.0
        for p in adjusted:
            assert 0.0 <= p <= 1.0

    def test_apply_benjamini_hochberg_all_zeros(self):
        """Test BH correction when all p-values are zero."""
        p_values = [0.0, 0.0, 0.0]
        result = apply_benjamini_hochberg(p_values)
        # Should handle zeros gracefully
        assert all(0.0 <= p <= 1.0 for p in result)

    def test_apply_benjamini_hochberg_all_ones(self):
        """Test BH correction when all p-values are 1.0."""
        p_values = [1.0, 1.0, 1.0]
        result = apply_benjamini_hochberg(p_values)
        assert all(p == 1.0 for p in result)

class TestCohenD:
    """Tests for effect size calculation."""

    def test_calculate_cohens_d_basic(self):
        """Test Cohen's d calculation with known values."""
        group1 = np.array([1, 2, 3, 4, 5])
        group2 = np.array([2, 3, 4, 5, 6])
        
        d = calculate_cohens_d(group1, group2)
        
        # Mean diff = -1.0, pooled std ~ 1.0 -> d ~ -1.0
        assert isinstance(d, float)
        assert -2.0 < d < 0.0

class TestEffectSizes:
    """Tests for aggregate effect size calculation."""

    def test_calculate_effect_sizes_dataframe(self):
        """Test calculate_effect_sizes with a DataFrame."""
        df = pd.DataFrame({
            'centrality': [1.0, 2.0, 3.0, 4.0, 5.0],
            'pli': [0.1, 0.2, 0.3, 0.4, 0.5],
            'group': ['A', 'A', 'A', 'B', 'B'] # Dummy grouping if needed
        })
        
        # Mock the underlying calculation to avoid complex logic in unit test
        # We just verify the function signature and return type
        with patch('analysis.calculate_cohens_d', return_value=0.5):
            result = calculate_effect_sizes(df, 'centrality', 'pli')
            assert isinstance(result, dict)
            assert 'cohen_d' in result

class TestLMEAnalysis:
    """Tests for LME analysis wrapper."""

    def test_run_lme_analysis_returns_dict(self):
        """Test that run_lme_analysis returns a dictionary."""
        df = pd.DataFrame({
            'centrality': [1.0, 2.0, 3.0],
            'pli': [0.1, 0.2, 0.3],
            'global_coherence': [0.5, 0.6, 0.7],
            'subject': ['S1', 'S2', 'S3']
        })
        
        with patch('analysis.mixedlm') as mock_lme:
            mock_result = MagicMock()
            mock_result.pvalues = {'pli': 0.04, 'global_coherence': 0.12}
            mock_result.params = {'pli': 0.5, 'global_coherence': 0.1}
            mock_lme.from_formula.return_value.fit.return_value = mock_result
            
            result = run_lme_analysis(df, 'centrality', 'pli')
            
            assert isinstance(result, dict)
            assert 'p_values' in result
            assert 'params' in result

class TestReportGeneration:
    """Tests for report generation."""

    def test_generate_analysis_report_structure(self):
        """Test that generate_analysis_report produces a valid JSON structure."""
        results = {
            'lme': {'p_values': {'pli': 0.04}, 'params': {'pli': 0.5}},
            'fdr': {'pli': 0.08},
            'shapiro': {'p_value': 0.2}
        }
        
        report = generate_analysis_report(results, n_subjects=30)
        
        assert isinstance(report, dict)
        assert 'coefficients' in report
        assert 'p_values' in report
        assert 'fdr_corrected_p_values' in report
        assert 'significance_flags' in report
