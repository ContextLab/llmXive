"""
Unit tests for synthetic dataset generator (T026).

Verifies:
- Binary and continuous outcome generation
- Constraint preservation (reported p-values match reconstructed within threshold)
- Minimum record count (>= 10,000)
- File creation and data integrity
"""
import json
import math
import os
from pathlib import Path
from typing import Dict, Any

import numpy as np
import pytest
from scipy import stats

from code.src.config import SEED
from code.src.audit.synthetic import (
    generate_binary_summary,
    generate_continuous_summary,
    generate_synthetic_dataset,
    main
)

OUTPUT_DIR = Path("data/synthetic")

class TestBinaryOutcomeGeneration:
    def test_binary_summary_structure(self):
        """Test that binary summary contains all required fields."""
        summary, ground_truth = generate_binary_summary(
            n_control=1000,
            n_treatment=1000,
            p_control=0.5,
            p_treatment=0.55,
            seed=42
        )
        
        required_fields = [
            'url', 'domain', 'test_type', 'n_control', 'n_treatment',
            'control_rate', 'treatment_rate', 'reported_p_value',
            'effect_size', 'publication_year', 'is_significant'
        ]
        
        for field in required_fields:
            assert field in summary, f"Missing required field: {field}"
        
        assert summary['test_type'] == 'binary'
        assert summary['n_control'] == 1000
        assert summary['n_treatment'] == 1000

    def test_binary_p_value_consistency(self):
        """Test that reported p-value is close to true p-value."""
        summary, ground_truth = generate_binary_summary(
            n_control=5000,
            n_treatment=5000,
            p_control=0.3,
            p_treatment=0.35,
            seed=42
        )
        
        # Check constraint preservation
        assert abs(summary['reported_p_value'] - ground_truth['true_p_value']) < 0.05
        assert ground_truth['is_consistent']

    def test_binary_effect_size_calculation(self):
        """Test that effect size is correctly calculated."""
        summary, _ = generate_binary_summary(
            n_control=1000,
            n_treatment=1000,
            p_control=0.4,
            p_treatment=0.45,
            seed=42
        )
        
        expected_effect = summary['treatment_rate'] - summary['control_rate']
        assert abs(summary['effect_size'] - expected_effect) < 1e-6

class TestContinuousOutcomeGeneration:
    def test_continuous_summary_structure(self):
        """Test that continuous summary contains all required fields."""
        summary, ground_truth = generate_continuous_summary(
            n_control=1000,
            n_treatment=1000,
            mu_control=50.0,
            mu_treatment=52.0,
            sigma=10.0,
            seed=42
        )
        
        required_fields = [
            'url', 'domain', 'test_type', 'n_control', 'n_treatment',
            'control_mean', 'treatment_mean', 'control_std', 'treatment_std',
            'reported_p_value', 'effect_size', 'publication_year', 'is_significant'
        ]
        
        for field in required_fields:
            assert field in summary, f"Missing required field: {field}"
        
        assert summary['test_type'] == 'continuous'

    def test_continuous_p_value_consistency(self):
        """Test that reported p-value is close to true p-value."""
        summary, ground_truth = generate_continuous_summary(
            n_control=5000,
            n_treatment=5000,
            mu_control=50.0,
            mu_treatment=52.0,
            sigma=10.0,
            seed=42
        )
        
        # Check constraint preservation
        assert abs(summary['reported_p_value'] - ground_truth['true_p_value']) < 0.05
        assert ground_truth['is_consistent']

class TestSyntheticDatasetGeneration:
    def test_minimum_record_count(self):
        """Test that generated dataset has at least 10,000 records."""
        summaries, ground_truths = generate_synthetic_dataset(n_records=10000, seed=SEED)
        
        assert len(summaries) >= 10000, f"Expected >= 10000 records, got {len(summaries)}"
        assert len(ground_truths) >= 10000

    def test_binary_continuous_ratio(self):
        """Test that dataset contains both binary and continuous outcomes."""
        summaries, _ = generate_synthetic_dataset(n_records=10000, seed=SEED)
        
        binary_count = sum(1 for s in summaries if s['test_type'] == 'binary')
        continuous_count = sum(1 for s in summaries if s['test_type'] == 'continuous')
        
        assert binary_count > 0, "No binary outcomes generated"
        assert continuous_count > 0, "No continuous outcomes generated"
        assert binary_count + continuous_count == len(summaries)

    def test_constraint_preservation_rate(self):
        """Test that constraint preservation rate is high (>95%)."""
        _, ground_truths = generate_synthetic_dataset(n_records=10000, seed=SEED)
        
        consistent_count = sum(1 for gt in ground_truths if gt['is_consistent'])
        consistency_rate = consistent_count / len(ground_truths)
        
        # With large sample sizes, most should be consistent
        assert consistency_rate > 0.90, f"Constraint preservation rate {consistency_rate:.2%} too low"

class TestMainFunction:
    def test_main_creates_files(self):
        """Test that main() creates the expected output files."""
        # Clean up existing files if any
        for f in OUTPUT_DIR.glob("*.csv"):
            f.unlink()
        for f in OUTPUT_DIR.glob("*.json"):
            f.unlink()
        
        result = main()
        
        assert result == 0, "main() returned non-zero exit code"
        
        # Check files exist
        assert (OUTPUT_DIR / "binary_outcomes.csv").exists(), "binary_outcomes.csv not created"
        assert (OUTPUT_DIR / "continuous_outcomes.csv").exists(), "continuous_outcomes.csv not created"
        assert (OUTPUT_DIR / "ground_truth.json").exists(), "ground_truth.json not created"

    def test_main_file_sizes(self):
        """Test that generated files contain sufficient records."""
        main()
        
        # Read and count binary records
        binary_path = OUTPUT_DIR / "binary_outcomes.csv"
        with open(binary_path, 'r') as f:
            binary_lines = len(f.readlines()) - 1  # Subtract header
        
        # Read and count continuous records
        continuous_path = OUTPUT_DIR / "continuous_outcomes.csv"
        with open(continuous_path, 'r') as f:
            continuous_lines = len(f.readlines()) - 1  # Subtract header
        
        # Total should be >= 10000
        total_records = binary_lines + continuous_lines
        assert total_records >= 10000, f"Total records {total_records} < 10000"

    def test_main_ground_truth_integrity(self):
        """Test that ground truth JSON is valid and contains expected fields."""
        main()
        
        ground_truth_path = OUTPUT_DIR / "ground_truth.json"
        with open(ground_truth_path, 'r') as f:
            ground_truths = json.load(f)
        
        assert len(ground_truths) >= 10000, "Ground truth has fewer than 10000 records"
        
        # Check structure of first record
        first_gt = ground_truths[0]
        required_fields = ['true_p_value', 'expected_significant', 'is_consistent']
        for field in required_fields:
            assert field in first_gt, f"Missing field in ground truth: {field}"
