import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.features.mass_balance import (
    calculate_random_fraction,
    check_mass_balance,
    validate_descriptor_mass_balance,
    validate_dataset_mass_balance,
    MAJOR_COMPONENTS,
    MASS_BALANCE_TOLERANCE
)
from code.data.models import TextureDescriptor


class TestCalculateRandomFraction:
    """Tests for calculate_random_fraction function."""

    def test_exact_balance(self):
        """Test when components sum to exactly 1.0."""
        volumes = {
            "brass": 0.25,
            "copper": 0.25,
            "s_component": 0.25,
            "goss": 0.25
        }
        random_frac = calculate_random_fraction(volumes)
        assert random_frac == 0.0

    def test_partial_balance(self):
        """Test when components sum to less than 1.0."""
        volumes = {
            "brass": 0.2,
            "copper": 0.3,
            "s_component": 0.1,
            "goss": 0.1
        }
        random_frac = calculate_random_fraction(volumes)
        assert abs(random_frac - 0.3) < 1e-6

    def test_excess_balance(self):
        """Test when components sum to more than 1.0 (should return 0)."""
        volumes = {
            "brass": 0.4,
            "copper": 0.4,
            "s_component": 0.3,
            "goss": 0.2
        }
        random_frac = calculate_random_fraction(volumes)
        assert random_frac == 0.0

    def test_missing_components(self):
        """Test when some components are missing from the dict."""
        volumes = {
            "brass": 0.5
            # copper, s_component, goss missing
        }
        random_frac = calculate_random_fraction(volumes)
        assert abs(random_frac - 0.5) < 1e-6


class TestCheckMassBalance:
    """Tests for check_mass_balance function."""

    def test_pass_within_tolerance(self):
        """Test mass balance passes when within tolerance."""
        volumes = {
            "brass": 0.25,
            "copper": 0.25,
            "s_component": 0.25,
            "goss": 0.24
        }
        is_valid, deviation, message = check_mass_balance(volumes, tolerance=0.01)
        
        assert is_valid is True
        assert abs(deviation - 0.01) < 1e-6
        assert "PASSED" in message

    def test_fail_outside_tolerance(self):
        """Test mass balance fails when outside tolerance."""
        volumes = {
            "brass": 0.2,
            "copper": 0.2,
            "s_component": 0.2,
            "goss": 0.15
        }
        is_valid, deviation, message = check_mass_balance(volumes, tolerance=0.01)
        
        assert is_valid is False
        assert deviation > 0.01
        assert "FAILED" in message

    def test_exact_balance(self):
        """Test mass balance with exact 1.0 sum."""
        volumes = {
            "brass": 0.25,
            "copper": 0.25,
            "s_component": 0.25,
            "goss": 0.25
        }
        is_valid, deviation, message = check_mass_balance(volumes)
        
        assert is_valid is True
        assert deviation == 0.0
        assert "PASSED" in message


class TestValidateDatasetMassBalance:
    """Tests for validate_dataset_mass_balance function."""

    def test_dataframe_validation(self):
        """Test validation on a DataFrame with multiple samples."""
        df = pd.DataFrame({
            "sample_id": ["S1", "S2", "S3"],
            "vol_brass": [0.25, 0.2, 0.3],
            "vol_copper": [0.25, 0.3, 0.2],
            "vol_s_component": [0.25, 0.2, 0.2],
            "vol_goss": [0.25, 0.1, 0.1]
        })
        
        result_df = validate_dataset_mass_balance(df)
        
        # Check that new columns were added
        assert "mass_balance_valid" in result_df.columns
        assert "mass_balance_deviation" in result_df.columns
        
        # S1 should pass (sum = 1.0)
        assert result_df.loc[0, "mass_balance_valid"] is True
        assert result_df.loc[0, "mass_balance_deviation"] == 0.0
        
        # S2 should fail (sum = 0.8, random = 0.2, total = 1.0) - Wait, this should pass
        # Let's recalculate: 0.2+0.3+0.2+0.1 = 0.8, random = 0.2, total = 1.0 -> PASS
        assert result_df.loc[1, "mass_balance_valid"] is True
        
        # S3: 0.3+0.2+0.2+0.1 = 0.8, random = 0.2, total = 1.0 -> PASS
        assert result_df.loc[2, "mass_balance_valid"] is True

    def test_dataframe_with_failure(self):
        """Test validation when some samples fail."""
        df = pd.DataFrame({
            "sample_id": ["S1", "S2"],
            "vol_brass": [0.25, 0.5],
            "vol_copper": [0.25, 0.4],
            "vol_s_component": [0.25, 0.3],
            "vol_goss": [0.25, 0.1]
        })
        
        result_df = validate_dataset_mass_balance(df)
        
        # S1 should pass
        assert result_df.loc[0, "mass_balance_valid"] is True
        
        # S2: 0.5+0.4+0.3+0.1 = 1.3, random = 0, total = 1.3 -> FAIL
        assert result_df.loc[1, "mass_balance_valid"] is False
        assert result_df.loc[1, "mass_balance_deviation"] > MASS_BALANCE_TOLERANCE


class TestValidateDescriptorMassBalance:
    """Tests for validate_descriptor_mass_balance function."""

    def test_valid_descriptor(self):
        """Test validation on a valid TextureDescriptor."""
        # Create a mock descriptor with volume_fractions
        descriptor = TextureDescriptor(
            sample_id="test_1",
            material="Al",
            reduction=50.0,
            texture_index=1.5,
            volume_fractions={
                "brass": 0.25,
                "copper": 0.25,
                "s_component": 0.25,
                "goss": 0.25
            }
        )
        
        is_valid, deviation, message = validate_descriptor_mass_balance(descriptor)
        
        assert is_valid is True
        assert deviation == 0.0

    def test_invalid_descriptor(self):
        """Test validation on an invalid TextureDescriptor."""
        descriptor = TextureDescriptor(
            sample_id="test_2",
            material="Cu",
            reduction=70.0,
            texture_index=2.0,
            volume_fractions={
                "brass": 0.5,
                "copper": 0.5,
                "s_component": 0.5,
                "goss": 0.5
            }
        )
        
        is_valid, deviation, message = validate_descriptor_mass_balance(descriptor)
        
        assert is_valid is False
        assert deviation > MASS_BALANCE_TOLERANCE

    def test_missing_volume_fractions(self):
        """Test validation when volume_fractions is missing."""
        descriptor = TextureDescriptor(
            sample_id="test_3",
            material="Ni",
            reduction=30.0,
            texture_index=1.2
            # volume_fractions not provided
        )
        
        # This should fail gracefully
        is_valid, deviation, message = validate_descriptor_mass_balance(descriptor)
        
        assert is_valid is False
        assert "missing" in message.lower()