import pytest
import pandas as pd
import numpy as np
import json
import os
import sys
from pathlib import Path

# Add project root to path if running from tests
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.entropy_glm import calculate_author_entropy, prepare_data_with_entropy, fit_entropy_glm

class TestCalculateAuthorEntropy:
    def test_uniform_distribution(self):
        # 3 authors, equal contributions -> log(3)
        contributions = pd.Series([100, 100, 100])
        entropy = calculate_author_entropy(contributions)
        expected = np.log(3)
        assert np.isclose(entropy, expected)

    def test_skewed_distribution(self):
        # One author dominates -> lower entropy
        contributions = pd.Series([900, 50, 50])
        entropy = calculate_author_entropy(contributions)
        # Should be less than log(3)
        assert entropy < np.log(3)
        assert entropy > 0

    def test_single_author(self):
        # Only one author -> entropy 0
        contributions = pd.Series([1000])
        entropy = calculate_author_entropy(contributions)
        assert entropy == 0.0

    def test_empty_series(self):
        contributions = pd.Series([])
        entropy = calculate_author_entropy(contributions)
        assert entropy == 0.0

    def test_zero_contributions(self):
        contributions = pd.Series([0, 0, 0])
        entropy = calculate_author_entropy(contributions)
        assert entropy == 0.0

class TestPrepareDataWithEntropy:
    def test_missing_contributions_column(self, tmp_path):
        # Create a dummy CSV without author_contributions
        csv_path = tmp_path / "test_data.csv"
        df = pd.DataFrame({
            'url': ['repo1'],
            'unique_authors': [1],
            'kloc': [10],
            'cve_count': [0]
        })
        df.to_csv(csv_path, index=False)
        
        output_path = tmp_path / "output.csv"
        
        with pytest.raises(ValueError, match="Column 'author_contributions' is missing"):
            prepare_data_with_entropy(str(csv_path), str(output_path))

    def test_calculates_entropy(self, tmp_path):
        # Create CSV with author_contributions
        csv_path = tmp_path / "test_data.csv"
        # JSON string of contributions
        df = pd.DataFrame({
            'url': ['repo1', 'repo2'],
            'unique_authors': [3, 2],
            'kloc': [10, 20],
            'cve_count': [1, 0],
            'author_contributions': ['[100, 100, 100]', '[500, 500]'] # Uniform distributions
        })
        df.to_csv(csv_path, index=False)
        
        output_path = tmp_path / "output.csv"
        
        result_df = prepare_data_with_entropy(str(csv_path), str(output_path))
        
        assert 'author_entropy' in result_df.columns
        # repo1: log(3), repo2: log(2)
        assert np.isclose(result_df.iloc[0]['author_entropy'], np.log(3))
        assert np.isclose(result_df.iloc[1]['author_entropy'], np.log(2))

class TestFitEntropyGlm:
    def test_model_fits(self, tmp_path):
        # Create a small dataset
        csv_path = tmp_path / "data.csv"
        df = pd.DataFrame({
            'url': [f'repo{i}' for i in range(20)],
            'unique_authors': [np.random.randint(2, 10) for _ in range(20)],
            'kloc': [np.random.uniform(1, 100) for _ in range(20)],
            'cve_count': [np.random.randint(0, 10) for _ in range(20)],
            'author_entropy': [np.random.uniform(0.5, 2.0) for _ in range(20)],
            'project_age': [np.random.uniform(1, 10) for _ in range(20)]
        })
        df.to_csv(csv_path, index=False)
        
        output_results = tmp_path / "results.json"
        
        results = fit_entropy_glm(str(csv_path), str(output_results))
        
        assert 'coefficients' in results
        assert 'author_entropy' in results['coefficients']
        assert 'converged' in results
        assert os.path.exists(output_results)