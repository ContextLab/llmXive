"""
Unit tests for Linear Mixed-Effects Model (LMM) fitting and p-value extraction.
Tests the StatisticalAnalyzer class in code/src/analysis.py.
"""

import pytest
import pandas as pd
import numpy as np
from statsmodels.formula.api import mixedlm
from statsmodels.regression.mixed_linear_model import MixedLMResults
import os
import sys
from pathlib import Path

# Ensure the code/src directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from analysis import StatisticalAnalyzer


class TestStatisticalAnalyzerLMM:
    """Tests for LMM model fitting and p-value extraction."""

    @pytest.fixture
    def sample_data(self):
        """Create a synthetic but realistic dataset for LMM testing."""
        np.random.seed(42)
        n_seeds = 10
        n_prompts_per_seed = 5
        
        data = []
        for seed in range(n_seeds):
            for prompt_id in range(n_prompts_per_seed):
                for strategy in ["Original_CDS", "Logical_Ascending", "Logical_Random"]:
                    # Simulate accuracy with some strategy effect and noise
                    base_acc = 0.7
                    strategy_effect = 0.0 if strategy == "Original_CDS" else (0.05 if strategy == "Logical_Ascending" else -0.02)
                    noise = np.random.normal(0, 0.05)
                    
                    data.append({
                        "accuracy": base_acc + strategy_effect + noise,
                        "strategy": strategy,
                        "model_type": "Reasoning" if seed % 2 == 0 else "Non-Reasoning",
                        "seed": seed,
                        "prompt_id": f"prompt_{seed}_{prompt_id}"
                    })
        
        return pd.DataFrame(data)

    @pytest.fixture
    def analyzer(self):
        """Create a StatisticalAnalyzer instance."""
        return StatisticalAnalyzer()

    def test_lmm_model_fitting_success(self, sample_data, analyzer):
        """Test that LMM model fitting completes without error."""
        formula = "accuracy ~ strategy + model_type + strategy:model_type + (1|seed) + (1|prompt_id)"
        
        # This should not raise an exception
        result = analyzer.fit_lmm(sample_data, formula)
        
        # Verify result is a MixedLMResults object
        assert isinstance(result, MixedLMResults)
        assert result is not None

    def test_lmm_p_value_extraction(self, sample_data, analyzer):
        """Test that p-values can be extracted for fixed effects."""
        formula = "accuracy ~ strategy + model_type + strategy:model_type + (1|seed) + (1|prompt_id)"
        result = analyzer.fit_lmm(sample_data, formula)
        
        # Extract p-values for fixed effects
        p_values = analyzer.extract_p_values(result)
        
        # Verify p-values are returned as a dictionary
        assert isinstance(p_values, dict)
        assert len(p_values) > 0
        
        # Verify all p-values are between 0 and 1
        for term, p_val in p_values.items():
            assert 0.0 <= p_val <= 1.0, f"P-value for {term} ({p_val}) is out of range"

    def test_lmm_interaction_term_significance(self, sample_data, analyzer):
        """Test that interaction term p-values are correctly extracted."""
        formula = "accuracy ~ strategy + model_type + strategy:model_type + (1|seed) + (1|prompt_id)"
        result = analyzer.fit_lmm(sample_data, formula)
        
        p_values = analyzer.extract_p_values(result)
        
        # Check that interaction terms are present in p-values
        interaction_terms = [term for term in p_values.keys() if "strategy" in term and "model_type" in term]
        assert len(interaction_terms) > 0, "No interaction terms found in p-values"
        
        # Verify all interaction terms have valid p-values
        for term in interaction_terms:
            assert 0.0 <= p_values[term] <= 1.0

    def test_lmm_model_convergence(self, sample_data, analyzer):
        """Test that the LMM model converges successfully."""
        formula = "accuracy ~ strategy + model_type + strategy:model_type + (1|seed) + (1|prompt_id)"
        result = analyzer.fit_lmm(sample_data, formula)
        
        # Check convergence status
        assert result.converged, "LMM model did not converge"

    def test_lmm_with_different_formulas(self, sample_data, analyzer):
        """Test LMM fitting with various model formulas."""
        formulas = [
            "accuracy ~ strategy + (1|seed)",
            "accuracy ~ strategy + model_type + (1|seed) + (1|prompt_id)",
            "accuracy ~ strategy * model_type + (1|seed)"
        ]
        
        for formula in formulas:
            result = analyzer.fit_lmm(sample_data, formula)
            assert isinstance(result, MixedLMResults)
            assert result.converged

    def test_p_value_extraction_format(self, sample_data, analyzer):
        """Test that p-values are extracted in the expected format."""
        formula = "accuracy ~ strategy + model_type + (1|seed)"
        result = analyzer.fit_lmm(sample_data, formula)
        p_values = analyzer.extract_p_values(result)
        
        # Verify structure
        assert "strategy" in p_values or any("strategy" in k for k in p_values.keys())
        assert "model_type" in p_values or any("model_type" in k for k in p_values.keys())
        
        # Verify all values are floats
        for term, p_val in p_values.items():
            assert isinstance(p_val, float), f"P-value for {term} is not a float"

    def test_lmm_with_small_dataset(self, analyzer):
        """Test LMM fitting with a very small dataset."""
        small_data = pd.DataFrame({
            "accuracy": [0.7, 0.75, 0.65, 0.8, 0.72, 0.68],
            "strategy": ["A", "A", "B", "B", "C", "C"],
            "model_type": ["R", "R", "R", "R", "R", "R"],
            "seed": [1, 1, 2, 2, 3, 3],
            "prompt_id": ["p1", "p2", "p3", "p4", "p5", "p6"]
        })
        
        formula = "accuracy ~ strategy + (1|seed)"
        result = analyzer.fit_lmm(small_data, formula)
        
        # Should still fit, though might have warnings
        assert isinstance(result, MixedLMResults)

    def test_p_value_extraction_empty_model(self, analyzer):
        """Test p-value extraction with a minimal model."""
        small_data = pd.DataFrame({
            "accuracy": [0.7, 0.75, 0.65],
            "strategy": ["A", "B", "C"],
            "model_type": ["R", "R", "R"],
            "seed": [1, 2, 3],
            "prompt_id": ["p1", "p2", "p3"]
        })
        
        formula = "accuracy ~ strategy"
        result = analyzer.fit_lmm(small_data, formula)
        p_values = analyzer.extract_p_values(result)
        
        assert isinstance(p_values, dict)
        assert len(p_values) > 0

    def test_lmm_error_handling_invalid_formula(self, sample_data, analyzer):
        """Test that invalid formulas raise appropriate errors."""
        with pytest.raises(Exception):
            # Invalid formula syntax
            formula = "accuracy ~ strategy + invalid_column + (1|seed)"
            analyzer.fit_lmm(sample_data, formula)

    def test_lmm_error_handling_missing_data(self, analyzer):
        """Test that missing data raises appropriate errors."""
        empty_data = pd.DataFrame()
        
        with pytest.raises(Exception):
            formula = "accuracy ~ strategy + (1|seed)"
            analyzer.fit_lmm(empty_data, formula)

    def test_p_value_extraction_with_categorical_variables(self, sample_data, analyzer):
        """Test p-value extraction when categorical variables are used."""
        formula = "accuracy ~ C(strategy) + C(model_type) + (1|seed)"
        result = analyzer.fit_lmm(sample_data, formula)
        p_values = analyzer.extract_p_values(result)
        
        assert isinstance(p_values, dict)
        assert len(p_values) > 0
        assert all(0.0 <= p <= 1.0 for p in p_values.values())

    def test_lmm_result_summary(self, sample_data, analyzer):
        """Test that model summary can be generated."""
        formula = "accuracy ~ strategy + model_type + (1|seed)"
        result = analyzer.fit_lmm(sample_data, formula)
        
        # Should be able to get summary without error
        summary = result.summary()
        assert summary is not None
        assert len(str(summary)) > 0