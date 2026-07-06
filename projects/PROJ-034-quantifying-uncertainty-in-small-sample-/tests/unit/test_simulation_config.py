"""
Unit tests for the SimulationConfig schema.
"""
import pytest
import numpy as np
from code.simulation.config import SimulationConfig


class TestSimulationConfigInitialization:
    """Tests for basic initialization and validation."""

    def test_valid_initialization(self):
        """Test that a valid config is created successfully."""
        config = SimulationConfig(N=50, n_predictors=5)
        assert config.N == 50
        assert config.n_predictors == 5
        assert config.intercept is True
        assert config.noise_std == 1.0
        assert config.rho is None
        assert len(config.true_coefficients) == 6  # 5 predictors + 1 intercept

    def test_no_intercept_initialization(self):
        """Test config creation without intercept."""
        config = SimulationConfig(N=30, n_predictors=3, intercept=False)
        assert config.intercept is False
        assert len(config.true_coefficients) == 3

    def test_custom_coefficients(self):
        """Test initialization with custom coefficients."""
        coeffs = [1.0, 2.0, 3.0]
        config = SimulationConfig(N=20, n_predictors=3, true_coefficients=coeffs, intercept=False)
        np.testing.assert_array_equal(config.true_coefficients, coeffs)

    def test_invalid_N(self):
        """Test that N <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="Sample size N must be positive"):
            SimulationConfig(N=0, n_predictors=5)
        
        with pytest.raises(ValueError, match="Sample size N must be positive"):
            SimulationConfig(N=-5, n_predictors=5)

    def test_invalid_n_predictors(self):
        """Test that n_predictors <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="Number of predictors must be positive"):
            SimulationConfig(N=50, n_predictors=0)

    def test_invalid_rho_range(self):
        """Test that rho outside (-1, 1) raises ValueError."""
        with pytest.raises(ValueError, match="Correlation rho must be in"):
            SimulationConfig(N=50, n_predictors=5, rho=1.0)
        
        with pytest.raises(ValueError, match="Correlation rho must be in"):
            SimulationConfig(N=50, n_predictors=5, rho=-1.0)
        
        with pytest.raises(ValueError, match="Correlation rho must be in"):
            SimulationConfig(N=50, n_predictors=5, rho=1.5)

    def test_invalid_noise_std(self):
        """Test that negative noise_std raises ValueError."""
        with pytest.raises(ValueError, match="Noise standard deviation must be non-negative"):
            SimulationConfig(N=50, n_predictors=5, noise_std=-1.0)

    def test_coefficient_length_mismatch(self):
        """Test that mismatched coefficient length raises ValueError."""
        # Too few coefficients
        with pytest.raises(ValueError, match="true_coefficients length"):
            SimulationConfig(N=50, n_predictors=5, true_coefficients=[1, 2], intercept=True)
        
        # Too many coefficients
        with pytest.raises(ValueError, match="true_coefficients length"):
            SimulationConfig(N=50, n_predictors=5, true_coefficients=[1, 2, 3, 4, 5, 6, 7], intercept=True)

class TestSerialization:
    """Tests for dict conversion methods."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = SimulationConfig(
            N=100,
            n_predictors=4,
            rho=0.5,
            noise_std=2.0,
            seed=42,
            intercept=False
        )
        data = config.to_dict()
        
        assert data["N"] == 100
        assert data["n_predictors"] == 4
        assert data["rho"] == 0.5
        assert data["noise_std"] == 2.0
        assert data["seed"] == 42
        assert data["intercept"] is False
        assert isinstance(data["true_coefficients"], list)

    def test_from_dict(self):
        """Test reconstruction from dictionary."""
        original = SimulationConfig(
            N=50,
            n_predictors=3,
            rho=0.3,
            noise_std=1.5,
            seed=123,
            intercept=True
        )
        
        data = original.to_dict()
        reconstructed = SimulationConfig.from_dict(data)
        
        assert reconstructed.N == original.N
        assert reconstructed.n_predictors == original.n_predictors
        assert reconstructed.rho == original.rho
        assert reconstructed.noise_std == original.noise_std
        assert reconstructed.seed == original.seed
        assert reconstructed.intercept == original.intercept
        np.testing.assert_array_almost_equal(
            reconstructed.true_coefficients, 
            original.true_coefficients
        )

    def test_from_dict_with_null_coefficients(self):
        """Test that from_dict handles missing coefficients by regenerating."""
        data = {
            "N": 20,
            "n_predictors": 2,
            "rho": None,
            "noise_std": 1.0,
            "seed": 999,
            "intercept": True
        }
        config = SimulationConfig.from_dict(data)
        # Should have generated default coefficients
        assert len(config.true_coefficients) == 3  # 2 predictors + 1 intercept
        assert config.seed == 999

class TestReproducibility:
    """Tests for seed-based reproducibility."""

    def test_seed_determinism(self):
        """Test that same seed produces same coefficients."""
        config1 = SimulationConfig(N=50, n_predictors=5, seed=42)
        config2 = SimulationConfig(N=50, n_predictors=5, seed=42)
        
        np.testing.assert_array_equal(
            config1.true_coefficients, 
            config2.true_coefficients
        )

    def test_different_seeds_different_coefficients(self):
        """Test that different seeds produce different coefficients."""
        config1 = SimulationConfig(N=50, n_predictors=5, seed=42)
        config2 = SimulationConfig(N=50, n_predictors=5, seed=43)
        
        # Probability of exact match is negligible
        assert not np.array_equal(
            config1.true_coefficients, 
            config2.true_coefficients
        )

class TestRepr:
    """Tests for string representation."""

    def test_repr_format(self):
        """Test that __repr__ returns a readable string."""
        config = SimulationConfig(N=50, n_predictors=5, rho=0.5, noise_std=1.0, seed=1)
        repr_str = repr(config)
        
        assert "SimulationConfig" in repr_str
        assert "N=50" in repr_str
        assert "n_predictors=5" in repr_str
        assert "rho=0.5" in repr_str