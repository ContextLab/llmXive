"""
Unit tests for empirical model fitting (Johnson-Cook, Zerilli-Armstrong).

This module tests the implementation of constitutive models used to predict
yield strength based on strain rate and temperature.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.modeling.empirical_models import (
    JohnsonCookModel,
    ZerilliArmstrongModel,
    fit_johnson_cook,
    fit_zerilli_armstrong
)


@pytest.fixture
def sample_dataset():
    """Create a realistic sample dataset for testing empirical models."""
    np.random.seed(42)
    n_samples = 100
    
    # Generate realistic strain rates (1e-3 to 1e4 s^-1)
    strain_rates = np.logspace(-3, 4, n_samples)
    
    # Generate realistic temperatures (200K to 600K)
    temperatures = np.random.uniform(200, 600, n_samples)
    
    # Generate base yield strength with some noise
    # Typical metals: 100-800 MPa
    base_strength = np.random.uniform(100, 800, n_samples)
    
    # Add strain rate dependence (positive correlation)
    strength = base_strength * (1 + 0.1 * np.log10(strain_rates))
    
    # Add temperature dependence (negative correlation)
    strength = strength * (1 - 0.0005 * (temperatures - 300))
    
    # Add noise
    strength += np.random.normal(0, 10, n_samples)
    
    df = pd.DataFrame({
        'yield_strength_mpa': strength,
        'strain_rate_s_inv': strain_rates,
        'temperature_k': temperatures,
        'alloy_family': np.random.choice(['AA-6061', 'AISI-4340', 'Ti-6Al-4V'], n_samples)
    })
    
    return df


@pytest.fixture
def small_dataset():
    """Create a small dataset for testing edge cases."""
    return pd.DataFrame({
        'yield_strength_mpa': [300.0, 320.0, 340.0],
        'strain_rate_s_inv': [1e-3, 1.0, 1e3],
        'temperature_k': [300.0, 300.0, 300.0],
        'alloy_family': ['AA-6061', 'AA-6061', 'AA-6061']
    })


class TestJohnsonCookModel:
    """Tests for Johnson-Cook constitutive model."""
    
    def test_initialization(self):
        """Test that JohnsonCookModel initializes with correct default parameters."""
        model = JohnsonCookModel()
        assert model.A is None
        assert model.B is None
        assert model.n is None
        assert model.C is None
        assert model.m is None
        assert model.reference_temp is None
        assert model.reference_strain_rate is None
        assert model.is_fitted is False
    
    def test_fit_basic(self, sample_dataset):
        """Test fitting Johnson-Cook model on sample data."""
        model = JohnsonCookModel()
        model.fit(
            sample_dataset['strain_rate_s_inv'],
            sample_dataset['temperature_k'],
            sample_dataset['yield_strength_mpa']
        )
        
        assert model.is_fitted is True
        assert model.A is not None
        assert model.B is not None
        assert model.n is not None
        assert model.C is not None
        assert model.m is not None
        assert model.reference_temp is not None
        assert model.reference_strain_rate is not None
    
    def test_fit_small_dataset(self, small_dataset):
        """Test fitting with minimal data points."""
        model = JohnsonCookModel()
        model.fit(
            small_dataset['strain_rate_s_inv'],
            small_dataset['temperature_k'],
            small_dataset['yield_strength_mpa']
        )
        
        assert model.is_fitted is True
    
    def test_predict_unfitted_raises_error(self):
        """Test that prediction raises error when model is not fitted."""
        model = JohnsonCookModel()
        with pytest.raises(RuntimeError, match="Model must be fitted before prediction"):
            model.predict(np.array([1.0]), np.array([300.0]))
    
    def test_predict_shapes(self, sample_dataset):
        """Test that prediction returns correct shape."""
        model = JohnsonCookModel()
        model.fit(
            sample_dataset['strain_rate_s_inv'],
            sample_dataset['temperature_k'],
            sample_dataset['yield_strength_mpa']
        )
        
        strain_rates = np.array([1e-3, 1.0, 1e3])
        temps = np.array([300.0, 300.0, 300.0])
        
        predictions = model.predict(strain_rates, temps)
        
        assert predictions.shape == (3,)
        assert np.all(predictions > 0)  # Yield strength should be positive
    
    def test_predict_single_point(self, sample_dataset):
        """Test prediction for a single data point."""
        model = JohnsonCookModel()
        model.fit(
            sample_dataset['strain_rate_s_inv'],
            sample_dataset['temperature_k'],
            sample_dataset['yield_strength_mpa']
        )
        
        prediction = model.predict(np.array([1.0]), np.array([300.0]))
        
        assert prediction.shape == (1,)
        assert np.isscalar(prediction[0]) or len(prediction) == 1
    
    def test_parameter_physical_constraints(self, sample_dataset):
        """Test that fitted parameters are physically reasonable."""
        model = JohnsonCookModel()
        model.fit(
            sample_dataset['strain_rate_s_inv'],
            sample_dataset['temperature_k'],
            sample_dataset['yield_strength_mpa']
        )
        
        # A should be positive (static yield strength)
        assert model.A > 0
        
        # C should be positive (strain rate hardening)
        assert model.C > 0
        
        # m should be positive (thermal softening)
        assert model.m > 0


class TestZerilliArmstrongModel:
    """Tests for Zerilli-Armstrong constitutive model."""
    
    def test_initialization(self):
        """Test that ZerilliArmstrongModel initializes correctly."""
        model = ZerilliArmstrongModel()
        assert model.C1 is None
        assert model.C2 is None
        assert model.C3 is None
        assert model.C4 is None
        assert model.C5 is None
        assert model.C6 is None
        assert model.is_fitted is False
    
    def test_fit_basic(self, sample_dataset):
        """Test fitting Zerilli-Armstrong model on sample data."""
        model = ZerilliArmstrongModel()
        model.fit(
            sample_dataset['strain_rate_s_inv'],
            sample_dataset['temperature_k'],
            sample_dataset['yield_strength_mpa']
        )
        
        assert model.is_fitted is True
        assert model.C1 is not None
        assert model.C2 is not None
        assert model.C3 is not None
    
    def test_fit_small_dataset(self, small_dataset):
        """Test fitting with minimal data points."""
        model = ZerilliArmstrongModel()
        model.fit(
            small_dataset['strain_rate_s_inv'],
            small_dataset['temperature_k'],
            small_dataset['yield_strength_mpa']
        )
        
        assert model.is_fitted is True
    
    def test_predict_unfitted_raises_error(self):
        """Test that prediction raises error when model is not fitted."""
        model = ZerilliArmstrongModel()
        with pytest.raises(RuntimeError, match="Model must be fitted before prediction"):
            model.predict(np.array([1.0]), np.array([300.0]))
    
    def test_predict_shapes(self, sample_dataset):
        """Test that prediction returns correct shape."""
        model = ZerilliArmstrongModel()
        model.fit(
            sample_dataset['strain_rate_s_inv'],
            sample_dataset['temperature_k'],
            sample_dataset['yield_strength_mpa']
        )
        
        strain_rates = np.array([1e-3, 1.0, 1e3])
        temps = np.array([300.0, 300.0, 300.0])
        
        predictions = model.predict(strain_rates, temps)
        
        assert predictions.shape == (3,)
        assert np.all(predictions > 0)
    
    def test_predict_single_point(self, sample_dataset):
        """Test prediction for a single data point."""
        model = ZerilliArmstrongModel()
        model.fit(
            sample_dataset['strain_rate_s_inv'],
            sample_dataset['temperature_k'],
            sample_dataset['yield_strength_mpa']
        )
        
        prediction = model.predict(np.array([1.0]), np.array([300.0]))
        
        assert prediction.shape == (1,)


class TestFitFunctions:
    """Tests for convenience fitting functions."""
    
    def test_fit_johnson_cook_function(self, sample_dataset):
        """Test the fit_johnson_cook convenience function."""
        model = fit_johnson_cook(
            sample_dataset['strain_rate_s_inv'],
            sample_dataset['temperature_k'],
            sample_dataset['yield_strength_mpa']
        )
        
        assert isinstance(model, JohnsonCookModel)
        assert model.is_fitted is True
    
    def test_fit_zerilli_armstrong_function(self, sample_dataset):
        """Test the fit_zerilli_armstrong convenience function."""
        model = fit_zerilli_armstrong(
            sample_dataset['strain_rate_s_inv'],
            sample_dataset['temperature_k'],
            sample_dataset['yield_strength_mpa']
        )
        
        assert isinstance(model, ZerilliArmstrongModel)
        assert model.is_fitted is True
    
    def test_fit_with_invalid_data_raises_error(self):
        """Test that fitting with invalid data raises appropriate errors."""
        # Empty arrays
        with pytest.raises(ValueError):
            fit_johnson_cook(
                np.array([]),
                np.array([]),
                np.array([])
            )
    
    def test_fit_with_mismatched_shapes_raises_error(self, sample_dataset):
        """Test that fitting with mismatched array shapes raises error."""
        with pytest.raises(ValueError):
            fit_johnson_cook(
                sample_dataset['strain_rate_s_inv'],
                sample_dataset['temperature_k'],
                sample_dataset['yield_strength_mpa'].values[:50]  # Wrong length
            )


class TestModelComparison:
    """Tests for comparing empirical models."""
    
    def test_both_models_fit_same_data(self, sample_dataset):
        """Test that both models can fit the same dataset."""
        jc_model = fit_johnson_cook(
            sample_dataset['strain_rate_s_inv'],
            sample_dataset['temperature_k'],
            sample_dataset['yield_strength_mpa']
        )
        
        za_model = fit_zerilli_armstrong(
            sample_dataset['strain_rate_s_inv'],
            sample_dataset['temperature_k'],
            sample_dataset['yield_strength_mpa']
        )
        
        assert jc_model.is_fitted is True
        assert za_model.is_fitted is True
        
        # Both should produce predictions
        strain_rates = np.array([1.0])
        temps = np.array([300.0])
        
        jc_pred = jc_model.predict(strain_rates, temps)
        za_pred = za_model.predict(strain_rates, temps)
        
        assert len(jc_pred) == 1
        assert len(za_pred) == 1
        assert jc_pred[0] > 0
        assert za_pred[0] > 0


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_extreme_strain_rates(self, sample_dataset):
        """Test fitting with extreme strain rate values."""
        extreme_data = sample_dataset.copy()
        extreme_data['strain_rate_s_inv'] = np.logspace(-10, 10, len(extreme_data))
        
        model = JohnsonCookModel()
        model.fit(
            extreme_data['strain_rate_s_inv'],
            extreme_data['temperature_k'],
            extreme_data['yield_strength_mpa']
        )
        
        assert model.is_fitted is True
    
    def test_constant_temperature(self):
        """Test fitting with constant temperature (isothermal)."""
        df = pd.DataFrame({
            'yield_strength_mpa': [300, 320, 340, 360, 380],
            'strain_rate_s_inv': [1e-3, 1e-2, 1e-1, 1.0, 10.0],
            'temperature_k': [300.0, 300.0, 300.0, 300.0, 300.0],
            'alloy_family': ['AA-6061'] * 5
        })
        
        model = JohnsonCookModel()
        model.fit(
            df['strain_rate_s_inv'],
            df['temperature_k'],
            df['yield_strength_mpa']
        )
        
        assert model.is_fitted is True
    
    def test_single_strain_rate(self):
        """Test fitting with single strain rate value."""
        df = pd.DataFrame({
            'yield_strength_mpa': [300, 310, 320, 330, 340],
            'strain_rate_s_inv': [1.0, 1.0, 1.0, 1.0, 1.0],
            'temperature_k': [300, 310, 320, 330, 340],
            'alloy_family': ['AA-6061'] * 5
        })
        
        model = JohnsonCookModel()
        model.fit(
            df['strain_rate_s_inv'],
            df['temperature_k'],
            df['yield_strength_mpa']
        )
        
        assert model.is_fitted is True