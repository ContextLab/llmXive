import pytest
import numpy as np
import os
import csv
from simulation_engine import count_type_i_and_type_ii_errors, save_error_counts, SimulationConfig
from simulation_engine import run_full_simulation_batch

class TestTypeITypeIIErrorCounting:
    """Test cases for Type I and Type II error counting logic (T021)."""

    def test_type_i_error_classification(self):
        """Test that Type I error is correctly identified when null is true and p < alpha."""
        p_value = 0.03
        null_is_true = True
        alpha = 0.05
        
        is_type_i, is_type_ii = count_type_i_and_type_ii_errors(p_value, null_is_true, alpha)
        
        assert is_type_i == True, "Should be Type I error when null is true and p < alpha"
        assert is_type_ii == False, "Should not be Type II error"

    def test_type_ii_error_classification(self):
        """Test that Type II error is correctly identified when null is false and p >= alpha."""
        p_value = 0.07
        null_is_true = False
        alpha = 0.05
        
        is_type_i, is_type_ii = count_type_i_and_type_ii_errors(p_value, null_is_true, alpha)
        
        assert is_type_i == False, "Should not be Type I error"
        assert is_type_ii == True, "Should be Type II error when null is false and p >= alpha"

    def test_correct_decision_null_true(self):
        """Test correct decision when null is true and p >= alpha."""
        p_value = 0.07
        null_is_true = True
        alpha = 0.05
        
        is_type_i, is_type_ii = count_type_i_and_type_ii_errors(p_value, null_is_true, alpha)
        
        assert is_type_i == False, "Should not be Type I error"
        assert is_type_ii == False, "Should not be Type II error"

    def test_correct_decision_null_false(self):
        """Test correct decision when null is false and p < alpha."""
        p_value = 0.03
        null_is_true = False
        alpha = 0.05
        
        is_type_i, is_type_ii = count_type_i_and_type_ii_errors(p_value, null_is_true, alpha)
        
        assert is_type_i == False, "Should not be Type I error"
        assert is_type_ii == False, "Should not be Type II error"

    def test_save_error_counts_creates_file(self, tmp_path):
        """Test that save_error_counts creates a valid CSV file."""
        error_counts_data = [
            {
                'sample_size': 50,
                'distribution_type': 'normal',
                'test_type': 't_test',
                'hypothesis_type': 'null',
                'type_i_count': 50,
                'type_ii_count': 0,
                'n_replicates': 1000
            }
        ]
        
        output_path = tmp_path / "error_counts.csv"
        save_error_counts(error_counts_data, str(output_path))
        
        assert output_path.exists(), "Output file should be created"
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 1, "Should have one row"
        assert rows[0]['sample_size'] == '50', "Sample size should be 50"
        assert rows[0]['type_i_count'] == '50', "Type I count should be 50"

    def test_error_counts_schema(self, tmp_path):
        """Test that error counts CSV has the correct schema."""
        error_counts_data = [
            {
                'sample_size': 100,
                'distribution_type': 'uniform',
                'test_type': 'anova',
                'hypothesis_type': 'alternative',
                'type_i_count': 0,
                'type_ii_count': 100,
                'n_replicates': 1000
            }
        ]
        
        output_path = tmp_path / "error_counts.csv"
        save_error_counts(error_counts_data, str(output_path))
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            
        expected_fields = ['sample_size', 'distribution_type', 'test_type', 'hypothesis_type', 'type_i_count', 'type_ii_count', 'n_replicates']
        assert fieldnames == expected_fields, f"Schema mismatch. Expected {expected_fields}, got {fieldnames}"

    def test_integration_error_counting_in_simulation(self, tmp_path):
        """Test that error counting works correctly in a full simulation run."""
        configs = [
            SimulationConfig(sample_size=30, distribution_type='normal', test_type='t_test', effect_size=0.0, n_replicates=100),
            SimulationConfig(sample_size=30, distribution_type='normal', test_type='t_test', effect_size=0.5, n_replicates=100),
        ]
        
        raw_pvalues_path = tmp_path / "raw_pvalues.csv"
        error_counts_path = tmp_path / "error_counts.csv"
        
        results = run_full_simulation_batch(configs, str(raw_pvalues_path), str(error_counts_path))
        
        assert len(results['error_counts']) == 2, "Should have error counts for both configurations"
        
        # Check that error_counts.csv was created and has data
        assert error_counts_path.exists(), "error_counts.csv should be created"
        
        with open(error_counts_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2, "Should have two rows in error_counts.csv"
        
        # Verify the null hypothesis row has Type I errors (should be around 5% for alpha=0.05)
        null_row = next(r for r in rows if r['hypothesis_type'] == 'null')
        type_i_rate = int(null_row['type_i_count']) / int(null_row['n_replicates'])
        
        # Allow some variance due to randomness, but should be in reasonable range
        assert 0.01 <= type_i_rate <= 0.10, f"Type I error rate should be around 0.05, got {type_i_rate}"
        
        # Verify the alternative hypothesis row has Type II errors
        alt_row = next(r for r in rows if r['hypothesis_type'] == 'alternative')
        type_ii_rate = int(alt_row['type_ii_count']) / int(alt_row['n_replicates'])
        
        # For effect_size=0.5 and n=30, we expect some power, so Type II should be < 1.0
        assert type_ii_rate < 1.0, "Type II error rate should be less than 1.0 for alternative hypothesis"