import os
import json
import tempfile
import pandas as pd
import pytest
from scipy.stats import uniform
from code.check_ks_pvalue import (
    load_association_results,
    check_significant_taxa,
    run_kolmogorov_smirnov_test,
    save_ks_results
)

class TestLoadAssociationResults:
    def test_load_valid_csv(self, tmp_path):
        # Create a temporary CSV file
        csv_path = tmp_path / "test_associations.csv"
        df = pd.DataFrame({
            'feature': ['taxon_a', 'taxon_b'],
            'pval_raw': [0.01, 0.05],
            'pval_adj': [0.02, 0.1]
        })
        df.to_csv(csv_path, index=False)
        
        loaded_df = load_association_results(str(csv_path))
        assert len(loaded_df) == 2
        assert 'pval_raw' in loaded_df.columns

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_association_results("nonexistent_file.csv")

class TestCheckSignificantTaxa:
    def test_has_significant_taxa(self):
        df = pd.DataFrame({
            'feature': ['taxon_a', 'taxon_b', 'taxon_c'],
            'pval_adj': [0.01, 0.06, 0.04]
        })
        assert check_significant_taxa(df, q_threshold=0.05) is True

    def test_no_significant_taxa(self):
        df = pd.DataFrame({
            'feature': ['taxon_a', 'taxon_b'],
            'pval_adj': [0.06, 0.08]
        })
        assert check_significant_taxa(df, q_threshold=0.05) is False

    def test_no_adj_column(self):
        df = pd.DataFrame({
            'feature': ['taxon_a'],
            'pval_raw': [0.01]
        })
        # Should return False and log warning
        assert check_significant_taxa(df, q_threshold=0.05) is False

class TestRunKolmogorovSmirnovTest:
    def test_uniform_distribution(self):
        # Generate truly uniform random data
        np.random.seed(42)
        uniform_data = pd.Series(np.random.uniform(0, 1, 1000))
        statistic, p_value = run_kolmogorov_smirnov_test(uniform_data)
        
        # For uniform data, p-value should be high (fail to reject null)
        assert p_value > 0.01  # Usually > 0.05 for uniform

    def test_non_uniform_distribution(self):
        # Generate skewed data (not uniform)
        skewed_data = pd.Series([0.01] * 500 + [0.99] * 500)
        statistic, p_value = run_kolmogorov_smirnov_test(skewed_data)
        
        # For non-uniform data, p-value should be low (reject null)
        assert p_value < 0.05

    def test_empty_series(self):
        empty_series = pd.Series([])
        statistic, p_value = run_kolmogorov_smirnov_test(empty_series)
        assert statistic == 0.0
        assert p_value == 1.0

class TestSaveKsResults:
    def test_save_results(self, tmp_path):
        output_path = tmp_path / "ks_results.json"
        save_ks_results(0.1, 0.03, str(output_path))
        
        assert output_path.exists()
        with open(output_path) as f:
            results = json.load(f)
        
        assert results['statistic'] == 0.1
        assert results['p_value'] == 0.03
        assert results['result'] == 'PASS'  # p < 0.05

    def test_save_fail_result(self, tmp_path):
        output_path = tmp_path / "ks_results_fail.json"
        save_ks_results(0.05, 0.2, str(output_path))
        
        with open(output_path) as f:
            results = json.load(f)
        
        assert results['result'] == 'FAIL'  # p >= 0.05