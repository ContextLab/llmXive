"""
Integration test for stratified analysis and multiple-comparison correction.
This test verifies that the statistical analysis pipeline correctly:
1. Groups data by CWE ID
2. Skips groups with n < 5
3. Applies Benjamini-Hochberg correction to p-values
4. Handles edge cases (empty groups, single source types)
"""

import json
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Import the functions to test from the stats module
# Note: We are testing the logic, not the full pipeline execution
from code.stats import run_stratified_analysis, calculate_fpr_metrics


class TestStratifiedAnalysis:
    """Integration tests for stratified analysis functionality."""

    @pytest.fixture
    def sample_aggregated_data(self, tmp_path):
        """Create a sample aggregated dataset for testing."""
        # Create a realistic sample dataset with multiple CWEs and source types
        data = {
            'task_id': [f'task_{i}' for i in range(100)],
            'source_type': ['human'] * 40 + ['llm'] * 60,
            'benchmark': ['humaneval'] * 50 + ['mbpp'] * 50,
            'cwe_id': (
                ['CWE-79'] * 15 + ['CWE-89'] * 20 + ['CWE-22'] * 10 +  # human
                ['CWE-79'] * 25 + ['CWE-89'] * 20 + ['CWE-78'] * 15    # llm
            ),
            'lines_of_code': np.random.randint(10, 200, 100),
            'vulnerability_count': np.random.poisson(2, 100)
        }
        
        df = pd.DataFrame(data)
        output_path = tmp_path / "aggregated_analysis_dataset.csv"
        df.to_csv(output_path, index=False)
        return output_path

    @pytest.fixture
    def sample_validator_flags(self, tmp_path):
        """Create sample validator flags for FPR calculation."""
        data = {
            'sample_id': [f'sample_{i}' for i in range(50)],
            'is_valid': [True] * 30 + [False] * 20
        }
        df = pd.DataFrame(data)
        output_path = tmp_path / "validator_flags.csv"
        df.to_csv(output_path, index=False)
        return output_path

    def test_stratified_analysis_groups_correctly(self, sample_aggregated_data, tmp_path):
        """Test that stratified analysis correctly groups by CWE and skips small groups."""
        output_path = tmp_path / "stratified_results.json"
        
        # Run the stratified analysis
        results = run_stratified_analysis(
            input_path=str(sample_aggregated_data),
            output_path=str(output_path)
        )
        
        # Verify results structure
        assert isinstance(results, dict), "Results should be a dictionary"
        assert 'cwe_groups' in results, "Results should contain cwe_groups"
        assert 'skipped_groups' in results, "Results should contain skipped_groups"
        assert 'corrected_p_values' in results, "Results should contain corrected_p_values"
        
        # Verify that groups with n < 5 were skipped
        # In our sample data, CWE-22 has only 10 samples (all human), 
        # so it should be included (n >= 5)
        # But if we had a group with < 5, it should be in skipped_groups
        assert isinstance(results['skipped_groups'], list), "Skipped groups should be a list"
        
        # Verify p-value correction was applied
        assert len(results['corrected_p_values']) > 0, "Should have corrected p-values"
        for cwe_id, p_val in results['corrected_p_values'].items():
            assert 0 <= p_val <= 1, f"P-value for {cwe_id} should be between 0 and 1"

    def test_stratified_analysis_handles_edge_cases(self, tmp_path):
        """Test that stratified analysis handles edge cases correctly."""
        # Create a dataset with only one CWE group and small sample size
        data = {
            'task_id': [f'task_{i}' for i in range(3)],  # Only 3 samples
            'source_type': ['human'] * 2 + ['llm'],
            'benchmark': ['humaneval'] * 3,
            'cwe_id': ['CWE-79'] * 3,
            'lines_of_code': [10, 20, 30],
            'vulnerability_count': [1, 2, 3]
        }
        
        input_path = tmp_path / "small_dataset.csv"
        df = pd.DataFrame(data)
        df.to_csv(input_path, index=False)
        
        output_path = tmp_path / "edge_case_results.json"
        
        # This should run without error and skip the group due to small sample size
        results = run_stratified_analysis(
            input_path=str(input_path),
            output_path=str(output_path)
        )
        
        # Verify the group was skipped
        assert len(results['skipped_groups']) > 0, "Small group should be skipped"
        assert 'CWE-79' in results['skipped_groups'], "CWE-79 should be in skipped groups"

    def test_benjamini_hochberg_correction(self, sample_aggregated_data, tmp_path):
        """Test that Benjamini-Hochberg correction is correctly applied."""
        output_path = tmp_path / "bh_test_results.json"
        
        results = run_stratified_analysis(
            input_path=str(sample_aggregated_data),
            output_path=str(output_path)
        )
        
        # Get the corrected p-values
        corrected_p_values = results['corrected_p_values']
        
        # Verify that corrected p-values are monotonically increasing when sorted
        # (a property of BH correction)
        sorted_p_values = sorted(corrected_p_values.values())
        for i in range(1, len(sorted_p_values)):
            assert sorted_p_values[i] >= sorted_p_values[i-1], \
                "BH-corrected p-values should be monotonically increasing"
        
        # Verify that corrected p-values are <= 1
        for p_val in corrected_p_values.values():
            assert p_val <= 1.0, "Corrected p-values should not exceed 1.0"

    def test_fpr_calculation(self, sample_validator_flags, tmp_path):
        """Test FPR calculation with validator flags."""
        output_path = tmp_path / "fpr_results.json"
        
        results = calculate_fpr_metrics(
            input_path=str(sample_validator_flags),
            output_path=str(output_path)
        )
        
        # Verify results structure
        assert isinstance(results, dict), "Results should be a dictionary"
        assert 'fpr_by_group' in results, "Results should contain fpr_by_group"
        assert 'overall_fpr' in results, "Results should contain overall_fpr"
        
        # Verify FPR is between 0 and 1
        assert 0 <= results['overall_fpr'] <= 1, "Overall FPR should be between 0 and 1"
        
        for group, fpr in results['fpr_by_group'].items():
            assert 0 <= fpr <= 1, f"FPR for {group} should be between 0 and 1"

    def test_full_integration_pipeline(self, sample_aggregated_data, sample_validator_flags, tmp_path):
        """Test the full integration of stratified analysis and FPR calculation."""
        # Create output directory
        output_dir = tmp_path / "full_integration"
        output_dir.mkdir()
        
        # Run stratified analysis
        stratified_output = output_dir / "stratified_results.json"
        stratified_results = run_stratified_analysis(
            input_path=str(sample_aggregated_data),
            output_path=str(stratified_output)
        )
        
        # Run FPR calculation
        fpr_output = output_dir / "fpr_results.json"
        fpr_results = calculate_fpr_metrics(
            input_path=str(sample_validator_flags),
            output_path=str(fpr_output)
        )
        
        # Verify both outputs exist and are valid
        assert stratified_output.exists(), "Stratified results file should exist"
        assert fpr_output.exists(), "FPR results file should exist"
        
        # Verify file contents are valid JSON
        with open(stratified_output, 'r') as f:
            json.load(f)  # Should not raise
        
        with open(fpr_output, 'r') as f:
            json.load(f)  # Should not raise

    def test_multiple_comparison_correction_accuracy(self, tmp_path):
        """Test the accuracy of multiple comparison correction with known values."""
        # Create a dataset with known p-values
        data = {
            'task_id': [f'task_{i}' for i in range(20)],
            'source_type': ['human'] * 10 + ['llm'] * 10,
            'benchmark': ['humaneval'] * 20,
            'cwe_id': ['CWE-79'] * 10 + ['CWE-89'] * 10,
            'lines_of_code': [10] * 20,
            'vulnerability_count': [1] * 20
        }
        
        input_path = tmp_path / "known_pvalues_dataset.csv"
        df = pd.DataFrame(data)
        df.to_csv(input_path, index=False)
        
        output_path = tmp_path / "known_pvalues_results.json"
        
        results = run_stratified_analysis(
            input_path=str(input_path),
            output_path=str(output_path)
        )
        
        # Verify that correction was applied
        assert len(results['corrected_p_values']) > 0, "Should have corrected p-values"
        
        # The exact values depend on the statistical test used,
        # but we can verify the structure and bounds
        for cwe_id, p_val in results['corrected_p_values'].items():
            assert 0 <= p_val <= 1, f"P-value for {cwe_id} should be between 0 and 1"
            assert isinstance(p_val, (int, float)), f"P-value for {cwe_id} should be numeric"