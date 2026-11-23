import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.robustness import (
    calculate_shannon_entropy,
    fit_negative_binomial_glm,
    extract_results,
    filter_zero_kloc
)

class TestShannonEntropy:
    def test_entropy_uniform_distribution(self):
        """Test entropy calculation with a known uniform distribution proxy."""
        # If unique_authors = 10, H = log(10)
        df = pd.DataFrame({
            'unique_authors': [10, 5, 1, 0, np.nan],
            'raw_line_count': [100, 200, 50, 10, 30]
        })
        
        result = calculate_shannon_entropy(df)
        
        # log(10) ~ 2.302
        assert abs(result.iloc[0]['entropy'] - np.log(10)) < 1e-5
        # log(5) ~ 1.609
        assert abs(result.iloc[1]['entropy'] - np.log(5)) < 1e-5
        # log(1) = 0
        assert result.iloc[2]['entropy'] == 0.0
        # log(0) -> 0
        assert result.iloc[3]['entropy'] == 0.0
        # log(nan) -> 0
        assert result.iloc[4]['entropy'] == 0.0

class TestFilterZeroKloc:
    def test_filter_zero_kloc(self):
        """Test that rows with kloc <= 0 are removed."""
        df = pd.DataFrame({
            'kloc': [10.5, 0.0, 5.2, -1.0, np.nan],
            'cve_count': [1, 2, 3, 4, 5]
        })
        
        result = filter_zero_kloc(df)
        
        assert len(result) == 1
        assert result.iloc[0]['kloc'] == 10.5

class TestGLMFit:
    def test_glm_fit_entropy(self):
        """Test that the GLM can be fitted with entropy as predictor."""
        # Create synthetic-like data (but valid for the function)
        # We need kloc > 0, entropy > 0, cve_count >= 0
        np.random.seed(42)
        n = 100
        data = {
            'entropy': np.random.uniform(0.5, 3.0, n),
            'project_age': np.random.uniform(1, 10, n),
            'release_count': np.random.randint(1, 20, n),
            'kloc': np.random.uniform(1.0, 100.0, n),
            'cve_count': np.random.poisson(2, n)
        }
        df = pd.DataFrame(data)
        
        # This should not raise an exception if the model fits
        result = fit_negative_binomial_glm(
            df, 
            response_col='cve_count',
            predictor_col='entropy',
            offset_col='kloc'
        )
        
        assert result is not None
        assert hasattr(result, 'params')
        
        # Check that entropy coefficient exists
        assert 'entropy' in result.model.exog_names

class TestExtractResults:
    def test_extract_results_structure(self):
        """Test that extract_results returns the expected dictionary structure."""
        # We need a mock result object or a real one. 
        # Since we can't easily mock statsmodels GLMResults perfectly without a fit,
        # we will rely on the test_glm_fit_entropy test to ensure the model works,
        # and here we just verify the extraction logic if we had a result.
        
        # Instead, let's create a minimal mock-like scenario by fitting a real small model
        np.random.seed(123)
        n = 50
        data = {
            'entropy': np.random.uniform(1, 2, n),
            'project_age': np.random.uniform(1, 5, n),
            'release_count': np.random.randint(1, 5, n),
            'kloc': np.random.uniform(1, 10, n),
            'cve_count': np.random.poisson(1, n)
        }
        df = pd.DataFrame(data)
        
        result = fit_negative_binomial_glm(
            df, 
            response_col='cve_count',
            predictor_col='entropy',
            offset_col='kloc'
        )
        
        extracted = extract_results(result, 'entropy')
        
        assert 'coefficient' in extracted
        assert 'std_error' in extracted
        assert 'p_value' in extracted
        assert 'confidence_interval_95' in extracted
        assert 'converged' in extracted
        assert isinstance(extracted['coefficient'], float)
        assert isinstance(extracted['p_value'], float)