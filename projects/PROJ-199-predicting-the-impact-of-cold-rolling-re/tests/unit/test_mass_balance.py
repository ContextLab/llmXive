import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os

# Import the module to test
from code.features.mass_balance import (
    calculate_random_fraction,
    check_mass_balance,
    validate_descriptor_mass_balance,
    validate_dataset_mass_balance,
    TOLERANCE
)


class TestCalculateRandomFraction:
    def test_normal_case(self):
        # Sum of knowns = 0.8, random should be 0.2
        result = calculate_random_fraction(0.2, 0.2, 0.2, 0.2)
        assert np.isclose(result, 0.2)

    def test_sum_exceeds_one(self):
        # Sum of knowns = 1.1, random should be -0.1
        result = calculate_random_fraction(0.3, 0.3, 0.3, 0.2)
        assert np.isclose(result, -0.1)

    def test_sum_less_than_one(self):
        # Sum of knowns = 0.5, random should be 0.5
        result = calculate_random_fraction(0.1, 0.1, 0.1, 0.2)
        assert np.isclose(result, 0.5)


class TestCheckMassBalance:
    def test_valid_balance(self):
        is_valid, reason = check_mass_balance(
            "sample_1", 0.2, 0.2, 0.2, 0.2, 0.2
        )
        assert is_valid is True
        assert "Valid" in reason

    def test_invalid_balance_high(self):
        # Sum = 1.05, deviation = 0.05 > 0.01
        is_valid, reason = check_mass_balance(
            "sample_2", 0.25, 0.25, 0.25, 0.25, 0.05
        )
        assert is_valid is False
        assert "Mass balance violation" in reason

    def test_invalid_balance_low(self):
        # Sum = 0.95, deviation = 0.05 > 0.01
        is_valid, reason = check_mass_balance(
            "sample_3", 0.15, 0.15, 0.15, 0.15, 0.35
        )
        assert is_valid is False
        assert "Mass balance violation" in reason

    def test_tolerance_boundary(self):
        # Sum = 1.01, deviation = 0.01 == tolerance (should be valid)
        is_valid, reason = check_mass_balance(
            "sample_4", 0.2, 0.2, 0.2, 0.2, 0.21
        )
        assert is_valid is True


class TestValidateDescriptorMassBalance:
    def setup_method(self):
        # Create a mock dataframe
        self.df_valid = pd.DataFrame({
            'sample_id': ['A', 'B'],
            'brass': [0.2, 0.3],
            'copper': [0.2, 0.1],
            's': [0.2, 0.2],
            'goss': [0.2, 0.2],
            'random': [0.2, 0.2]
        })

        self.df_invalid = pd.DataFrame({
            'sample_id': ['C', 'D'],
            'brass': [0.5, 0.1],
            'copper': [0.5, 0.1],
            's': [0.5, 0.1],
            'goss': [0.5, 0.1],
            'random': [0.5, 0.7] # D is valid (sum=1.0), C is invalid (sum=2.0)
        })

        self.df_mixed = pd.DataFrame({
            'sample_id': ['E', 'F', 'G'],
            'brass': [0.2, 0.5, 0.1],
            'copper': [0.2, 0.1, 0.1],
            's': [0.2, 0.1, 0.1],
            'goss': [0.2, 0.1, 0.1],
            'random': [0.2, 0.7, 0.7] # E valid, F invalid (1.5), G valid
        })

    def test_all_valid(self):
        valid_df, excluded = validate_descriptor_mass_balance(self.df_valid)
        assert len(valid_df) == 2
        assert len(excluded) == 0

    def test_all_invalid(self):
        valid_df, excluded = validate_descriptor_mass_balance(self.df_invalid)
        # C is invalid, D is valid (0.1+0.1+0.1+0.1+0.7 = 1.1 -> invalid? wait. 0.1*4=0.4, +0.7=1.1. Invalid)
        # Actually D: 0.1+0.1+0.1+0.1+0.7 = 1.1. Deviation 0.1 > 0.01. Invalid.
        # So both are invalid.
        assert len(valid_df) == 0
        assert len(excluded) == 2

    def test_mixed_validity(self):
        valid_df, excluded = validate_descriptor_mass_balance(self.df_mixed)
        # E: 0.8+0.2=1.0 (Valid)
        # F: 1.5 (Invalid)
        # G: 0.4+0.7=1.1 (Invalid)
        assert len(valid_df) == 1
        assert valid_df['sample_id'].iloc[0] == 'E'
        assert len(excluded) == 2
        assert excluded[0]['sample_id'] == 'F'
        assert excluded[1]['sample_id'] == 'G'

    def test_missing_columns(self):
        bad_df = pd.DataFrame({'sample_id': ['X'], 'brass': [0.5]})
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_descriptor_mass_balance(bad_df)


class TestValidateDatasetMassBalanceIntegration:
    def test_full_flow(self, tmp_path):
        # Create input CSV
        input_data = {
            'sample_id': ['S1', 'S2', 'S3'],
            'brass': [0.2, 0.5, 0.1],
            'copper': [0.2, 0.1, 0.1],
            's': [0.2, 0.1, 0.1],
            'goss': [0.2, 0.1, 0.1],
            'random': [0.2, 0.7, 0.7]
        }
        df = pd.DataFrame(input_data)
        input_path = tmp_path / "descriptors.csv"
        df.to_csv(input_path, index=False)

        output_report_path = tmp_path / "mass_balance_report.json"

        # Run validation
        success = validate_dataset_mass_balance(
            descriptors_path=str(input_path),
            output_report_path=str(output_report_path)
        )

        # Assertions
        assert success is True
        assert output_report_path.exists()

        # Verify report content
        with open(output_report_path) as f:
            report = json.load(f)

        assert report['total_samples'] == 3
        assert report['valid_samples'] == 1
        assert report['excluded_samples_count'] == 2
        assert report['excluded_samples'][0]['sample_id'] == 'S2'
        assert report['excluded_samples'][1]['sample_id'] == 'S3'

        # Verify cleaned CSV exists
        cleaned_path = tmp_path / "descriptors_cleaned.csv"
        assert cleaned_path.exists()
        cleaned_df = pd.read_csv(cleaned_path)
        assert len(cleaned_df) == 1
        assert cleaned_df['sample_id'].iloc[0] == 'S1'