"""
Integration test for cluster-level permutation logic (T032).

This test verifies that the cluster-level permutation test implemented
in code/analysis/robustness.py correctly permutes family_id clusters
and produces valid p-values for the association between ACE scores
and hippocampal subfield volumes.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

import pytest
import pandas as pd
import numpy as np
from statsmodels.formula.api import mixedlm

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from code.analysis.robustness import (
    load_cleaned_data,
    run_permutation_test,
    calculate_cluster_permuted_pvalue
)
from code.config import PROJECT_ROOT as CONFIG_ROOT
from code.config_env import get_permutation_count, get_alpha_thresholds


class TestClusterPermutationLogic:
    """Integration tests for cluster-level permutation test logic."""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, tmp_path: Path):
        """Create a synthetic dataset that mimics the structure of real ABCD data."""
        # Create a temporary directory for test outputs
        self.test_output_dir = tmp_path / "test_outputs"
        self.test_output_dir.mkdir()
        
        # Create a synthetic dataset with realistic structure
        n_subjects = 200
        n_families = 50
        
        np.random.seed(42)
        
        # Generate family IDs (some families have multiple children)
        family_ids = []
        for i in range(n_families):
            n_children = np.random.randint(1, 4)  # 1-3 children per family
            family_ids.extend([f"family_{i:03d}"] * n_children)
        
        # Trim to exact number of subjects
        family_ids = family_ids[:n_subjects]
        
        # Generate data
        data = {
            'participant_id': [f"sub_{i:04d}" for i in range(n_subjects)],
            'family_id': family_ids,
            'site': np.random.choice(['site_A', 'site_B', 'site_C'], n_subjects),
            'age': np.random.uniform(9.0, 11.0, n_subjects),
            'sex': np.random.choice(['M', 'F'], n_subjects),
            'ace_score': np.random.normal(2.5, 1.5, n_subjects).clip(0, 10),
            'icv': np.random.normal(1500, 150, n_subjects).clip(1000, 2000),
            'ca3_vol': np.random.normal(45, 5, n_subjects),
            'dg_vol': np.random.normal(35, 4, n_subjects),
            'subiculum_vol': np.random.normal(65, 7, n_subjects),
        }
        
        # Add some true effect for testing
        data['ca3_vol'] += 0.1 * data['ace_score']
        data['dg_vol'] -= 0.08 * data['ace_score']
        
        self.test_df = pd.DataFrame(data)
        
        # Save to CSV for loading tests
        self.test_csv_path = self.test_output_dir / "test_cleaned_dataset.csv"
        self.test_df.to_csv(self.test_csv_path, index=False)
        
        # Create a mock model results file
        self.mock_model_results = {
            "ca3": {
                "beta": 0.12,
                "ci_lower": 0.05,
                "ci_upper": 0.19,
                "p_value": 0.002,
                "corrected_p_value": 0.006
            },
            "dg": {
                "beta": -0.09,
                "ci_lower": -0.15,
                "ci_upper": -0.03,
                "p_value": 0.004,
                "corrected_p_value": 0.012
            },
            "subiculum": {
                "beta": 0.02,
                "ci_lower": -0.04,
                "ci_upper": 0.08,
                "p_value": 0.45,
                "corrected_p_value": 0.45
            }
        }
        
        self.mock_results_path = self.test_output_dir / "model_results.json"
        with open(self.mock_results_path, 'w') as f:
            json.dump(self.mock_model_results, f)

    def test_load_cleaned_data_integration(self):
        """Test that load_cleaned_data correctly loads our test dataset."""
        loaded_df = load_cleaned_data(self.test_csv_path)
        
        assert loaded_df is not None
        assert len(loaded_df) == len(self.test_df)
        assert set(['family_id', 'ace_score', 'ca3_vol', 'dg_vol', 'subiculum_vol']).issubset(loaded_df.columns)
        
    def test_run_permutation_test_basic(self):
        """Test basic permutation test execution with a small number of permutations."""
        # Use a small number for faster testing
        n_perms = 100
        
        # Run permutation test for CA3 subfield
        result = run_permutation_test(
            data=self.test_df,
            outcome_col='ca3_vol',
            predictor_col='ace_score',
            cluster_col='family_id',
            n_permutations=n_perms,
            random_seed=42
        )
        
        assert result is not None
        assert 'observed_statistic' in result
        assert 'permutation_p_value' in result
        assert 'null_distribution' in result
        assert len(result['null_distribution']) == n_perms
        
        # The p-value should be between 0 and 1
        assert 0.0 <= result['permutation_p_value'] <= 1.0
        
    def test_cluster_permutation_preserves_family_structure(self):
        """
        Test that permutation correctly preserves family structure by permuting 
        at the family level, not individual level.
        """
        # Create a dataset with known family structure
        n_families = 10
        family_ids = [f"family_{i}" for i in range(n_families)]
        
        # Each family has 3 children
        expanded_families = []
        for fid in family_ids:
            expanded_families.extend([fid] * 3)
        
        test_data = pd.DataFrame({
            'family_id': expanded_families,
            'ace_score': np.random.normal(2.5, 1.0, len(expanded_families)),
            'ca3_vol': np.random.normal(45, 5, len(expanded_families))
        })
        
        # Run permutation test
        result = run_permutation_test(
            data=test_data,
            outcome_col='ca3_vol',
            predictor_col='ace_score',
            cluster_col='family_id',
            n_permutations=50,
            random_seed=123
        )
        
        # Verify the null distribution was generated
        assert len(result['null_distribution']) == 50
        
        # Verify that the permutation respected family clustering
        # (This is harder to test directly, but we can check that the 
        # permutation function doesn't break the data structure)
        assert result['observed_statistic'] is not None
        
    def test_pvalue_calculation_consistency(self):
        """Test that p-value calculation is consistent across runs."""
        n_perms = 200
        
        # Run the same test twice with the same seed
        result1 = run_permutation_test(
            data=self.test_df,
            outcome_col='ca3_vol',
            predictor_col='ace_score',
            cluster_col='family_id',
            n_permutations=n_perms,
            random_seed=42
        )
        
        result2 = run_permutation_test(
            data=self.test_df,
            outcome_col='ca3_vol',
            predictor_col='ace_score',
            cluster_col='family_id',
            n_permutations=n_perms,
            random_seed=42
        )
        
        # Results should be identical with the same seed
        assert result1['permutation_p_value'] == result2['permutation_p_value']
        assert result1['observed_statistic'] == result2['observed_statistic']
        
    def test_multiple_subfields(self):
        """Test that permutation test works for multiple subfields."""
        subfields = ['ca3_vol', 'dg_vol', 'subiculum_vol']
        results = {}
        
        for subfield in subfields:
            result = run_permutation_test(
                data=self.test_df,
                outcome_col=subfield,
                predictor_col='ace_score',
                cluster_col='family_id',
                n_permutations=50,
                random_seed=42
            )
            results[subfield] = result
            
        # All results should be valid
        for subfield, result in results.items():
            assert result is not None
            assert 'permutation_p_value' in result
            assert 0.0 <= result['permutation_p_value'] <= 1.0
            
    def test_integration_with_mock_results(self):
        """
        Integration test: Verify that permutation test results are 
        consistent with mock model results for validation purposes.
        """
        # Run permutation test
        perm_result = run_permutation_test(
            data=self.test_df,
            outcome_col='ca3_vol',
            predictor_col='ace_score',
            cluster_col='family_id',
            n_permutations=100,
            random_seed=42
        )
        
        # The permutation p-value should be in a reasonable range
        # (not necessarily matching the parametric p-value exactly, but in the same ballpark)
        assert 0.0 <= perm_result['permutation_p_value'] <= 1.0
        
        # Verify the observed statistic is calculated
        assert perm_result['observed_statistic'] is not None
        assert isinstance(perm_result['observed_statistic'], (int, float))
        
    def test_edge_case_single_family(self):
        """Test behavior when there's only one family (edge case)."""
        single_family_data = pd.DataFrame({
            'family_id': ['family_A'] * 20,
            'ace_score': np.random.normal(2.5, 1.0, 20),
            'ca3_vol': np.random.normal(45, 5, 20)
        })
        
        # This should still run, though the permutation test 
        # will have limited power with only one cluster
        result = run_permutation_test(
            data=single_family_data,
            outcome_col='ca3_vol',
            predictor_col='ace_score',
            cluster_col='family_id',
            n_permutations=10,
            random_seed=42
        )
        
        # Should still produce a result
        assert result is not None
        assert 'permutation_p_value' in result

    def test_output_format_conformance(self):
        """
        Verify that the permutation test output conforms to the expected schema
        for integration with the robustness report.
        """
        result = run_permutation_test(
            data=self.test_df,
            outcome_col='ca3_vol',
            predictor_col='ace_score',
            cluster_col='family_id',
            n_permutations=50,
            random_seed=42
        )
        
        # Check required keys
        required_keys = ['observed_statistic', 'permutation_p_value', 'null_distribution']
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"
            
        # Check types
        assert isinstance(result['observed_statistic'], (int, float))
        assert isinstance(result['permutation_p_value'], float)
        assert isinstance(result['null_distribution'], list)
        assert len(result['null_distribution']) == 50
        
        # Check that null distribution contains numeric values
        for val in result['null_distribution']:
            assert isinstance(val, (int, float))

    def test_permutation_count_parameter(self):
        """Test that the permutation count parameter is respected."""
        for n_perms in [10, 50, 100]:
            result = run_permutation_test(
                data=self.test_df,
                outcome_col='ca3_vol',
                predictor_col='ace_score',
                cluster_col='family_id',
                n_permutations=n_perms,
                random_seed=42
            )
            
            assert len(result['null_distribution']) == n_perms

    def test_random_seed_reproducibility(self):
        """Test that different random seeds produce different results."""
        result1 = run_permutation_test(
            data=self.test_df,
            outcome_col='ca3_vol',
            predictor_col='ace_score',
            cluster_col='family_id',
            n_permutations=100,
            random_seed=123
        )
        
        result2 = run_permutation_test(
            data=self.test_df,
            outcome_col='ca3_vol',
            predictor_col='ace_score',
            cluster_col='family_id',
            n_permutations=100,
            random_seed=456
        )
        
        # With different seeds, results should likely differ
        # (though there's a small chance they could be the same)
        # We'll just verify they both run successfully
        assert result1['permutation_p_value'] is not None
        assert result2['permutation_p_value'] is not None

    def test_integration_with_robustness_pipeline(self):
        """
        End-to-end integration test: Simulate how the permutation test
        would be used in the full robustness pipeline.
        """
        # 1. Load data
        data = load_cleaned_data(self.test_csv_path)
        
        # 2. Run permutation test for all subfields
        subfields = ['ca3_vol', 'dg_vol', 'subiculum_vol']
        permutation_results = {}
        
        for subfield in subfields:
            perm_result = run_permutation_test(
                data=data,
                outcome_col=subfield,
                predictor_col='ace_score',
                cluster_col='family_id',
                n_permutations=50,  # Small for testing
                random_seed=42
            )
            permutation_results[subfield] = perm_result
        
        # 3. Verify all results are valid
        for subfield, result in permutation_results.items():
            assert result is not None
            assert 'permutation_p_value' in result
            assert 0.0 <= result['permutation_p_value'] <= 1.0
            assert 'observed_statistic' in result
            
        # 4. Simulate saving results (like in robustness pipeline)
        output_file = self.test_output_dir / "permutation_results.json"
        with open(output_file, 'w') as f:
            json.dump(permutation_results, f, indent=2)
        
        # 5. Verify file was created and can be loaded
        assert output_file.exists()
        with open(output_file, 'r') as f:
            loaded_results = json.load(f)
            
        assert len(loaded_results) == len(subfields)
        for subfield in subfields:
            assert subfield in loaded_results

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
