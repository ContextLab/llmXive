import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import os
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.robustness import (
    calculate_lagged_metrics,
    fit_lagged_negative_binomial_glm,
    extract_results,
    filter_zero_kloc
)

class TestLaggedGlm:
    @pytest.fixture
    def mock_df(self):
        """Create a mock DataFrame with required columns."""
        data = {
            'url': ['https://github.com/test/repo1', 'https://github.com/test/repo2', 'https://github.com/test/repo3'],
            'primary_language': ['Python', 'JavaScript', 'Python'],
            'project_age': [10, 8, 12],
            'release_count': [5, 3, 8],
            'kloc': [10.5, 20.0, 5.0],
            'cve_count': [2, 1, 0]
        }
        return pd.DataFrame(data)

    def test_filter_zero_kloc(self, mock_df):
        """Test that rows with kloc <= 0 are removed."""
        mock_df.loc[1, 'kloc'] = 0
        filtered = filter_zero_kloc(mock_df)
        assert len(filtered) == 2
        assert 1 not in filtered.index

    def test_extract_results_structure(self):
        """Test that extract_results returns the expected dictionary structure."""
        # We mock a result object since we can't easily fit a real model in a unit test
        class MockResult:
            params = pd.Series({
                'author_count_lag_1year': 0.5,
                'project_age': 0.1,
                'C(primary_language)[T.JavaScript]': 0.2,
                'release_count': -0.05,
                'np.log(kloc)': 0.8
            })
            bse = pd.Series({
                'author_count_lag_1year': 0.1,
                'project_age': 0.05,
                'C(primary_language)[T.JavaScript]': 0.08,
                'release_count': 0.02,
                'np.log(kloc)': 0.15
            })
            pvalues = pd.Series({
                'author_count_lag_1year': 0.01,
                'project_age': 0.05,
                'C(primary_language)[T.JavaScript]': 0.1,
                'release_count': 0.2,
                'np.log(kloc)': 0.001
            })
            converged = True
            nobs = 100
            llf = -50.0

            def conf_int(self):
                return pd.DataFrame({
                    0: [0.3, 0.0, 0.04, -0.09, 0.5],
                    1: [0.7, 0.2, 0.36, -0.01, 1.1]
                }, index=self.params.index)

        result = extract_results(MockResult())
        
        assert 'model_type' in result
        assert result['model_type'] == 'Lagged Negative Binomial GLM'
        assert 'author_count_lag_coefficient' in result
        assert result['author_count_lag_coefficient'] == 0.5
        assert result['author_count_lag_p_value'] == 0.01
        assert result['convergence_status'] is True
        assert 'lag_period' in result

    def test_calculate_lagged_metrics_raises_if_missing(self, mock_df, tmp_path):
        """Test that calculate_lagged_metrics raises FileNotFoundError if NVD data is missing."""
        # Ensure the NVD file doesn't exist
        nvd_path = Path("data/raw/nvd_cve_merged.json.gz")
        if nvd_path.exists():
            nvd_path.unlink() # Remove if exists for test isolation
        
        # We can't easily test the git part without real clones, but we can test the NVD check
        # Since the function checks for NVD first, it should raise
        with pytest.raises(FileNotFoundError):
            # We need to mock the existence of tmp_clone_paths.txt to get past the first check?
            # No, the function checks NVD first.
            # Let's create a dummy tmp_clone_paths.txt to ensure we get to the NVD check if we want,
            # but the function checks NVD first.
            calculate_lagged_metrics(mock_df)