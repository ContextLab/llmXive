"""
Tests for the configuration module.
"""

import pytest
import numpy as np
from code.config import (
    NumericalSettings,
    SimulationConfig,
    AnalysisConfig,
    numerical_settings,
    simulation_config,
    analysis_config,
    set_simulation_seed,
    set_noise_levels,
    set_N_oscillators,
    get_full_config,
)


class TestNumericalSettings:
    """Tests for NumericalSettings dataclass."""
    
    def test_default_values(self):
        """Test that default tolerances match specification."""
        settings = NumericalSettings()
        assert settings.rtol == 1e-9
        assert settings.atol == 1e-12
        assert settings.method == "DOP853"
    
    def test_invalid_tolerance_negative(self):
        """Test that negative tolerances raise ValueError."""
        with pytest.raises(ValueError):
            NumericalSettings(rtol=-1e-9)
        with pytest.raises(ValueError):
            NumericalSettings(atol=-1e-12)
    
    def test_invalid_tolerance_too_loose(self):
        """Test that tolerances that are too loose raise ValueError."""
        with pytest.raises(ValueError):
            NumericalSettings(rtol=1e-2)
        with pytest.raises(ValueError):
            NumericalSettings(atol=1e-2)
    
    def test_valid_custom_settings(self):
        """Test creating settings with valid custom values."""
        settings = NumericalSettings(rtol=1e-8, atol=1e-10, method="RK45")
        assert settings.rtol == 1e-8
        assert settings.atol == 1e-10
        assert settings.method == "RK45"


class TestSimulationConfig:
    """Tests for SimulationConfig dataclass."""
    
    def test_default_values(self):
        """Test default Lorenz parameters and settings."""
        config = SimulationConfig()
        assert config.sigma == 10.0
        assert config.rho == 28.0
        assert config.beta == 8.0 / 3.0
        assert config.t_max == 1000.0
        assert config.dt_output == 0.01
        assert config.seed == 42
        assert config.N_oscillators == 5
        assert config.coupling_topology == "ring"
    
    def test_validate_positive_parameters(self):
        """Test validation of positive parameters."""
        config = SimulationConfig()
        config.validate()  # Should not raise
    
    def test_validate_negative_sigma(self):
        """Test validation rejects negative sigma."""
        config = SimulationConfig(sigma=-10.0)
        with pytest.raises(ValueError):
            config.validate()
    
    def test_validate_zero_N(self):
        """Test validation rejects N_oscillators < 1."""
        config = SimulationConfig(N_oscillators=0)
        with pytest.raises(ValueError):
            config.validate()
    
    def test_validate_negative_noise(self):
        """Test validation rejects negative noise levels."""
        config = SimulationConfig(noise_levels=[0.1, -0.1])
        with pytest.raises(ValueError):
            config.validate()
    
    def test_validate_threshold_order(self):
        """Test validation ensures warning threshold < error threshold."""
        config = SimulationConfig(
            high_noise_warning_threshold=0.5,
            high_noise_error_threshold=0.3
        )
        with pytest.raises(ValueError):
            config.validate()
    
    def test_noise_levels_default(self):
        """Test that default noise levels are set correctly."""
        config = SimulationConfig()
        expected = [1e-4, 1e-3, 1e-2, 1e-1, 0.5, 1.0]
        assert config.noise_levels == expected
    
    def test_ftle_window_sizes_default(self):
        """Test default FTLE window sizes."""
        config = SimulationConfig()
        assert config.ftle_window_sizes == [500, 1000, 5000]
    
    def test_num_trials_default(self):
        """Test default number of trials per noise level."""
        config = SimulationConfig()
        # This is set in AnalysisConfig, but we check simulation config has no negative trials
        assert config.num_trials_per_noise == 30


class TestAnalysisConfig:
    """Tests for AnalysisConfig dataclass."""
    
    def test_default_values(self):
        """Test default analysis configuration."""
        config = AnalysisConfig()
        assert config.baseline_convergence_tolerance == 1e-6
        assert config.baseline_min_T == 5000
        assert config.num_trials_per_noise == 30
        assert config.plot_dpi == 300
        assert config.plot_style == "seaborn-v0_8-whitegrid"
    
    def test_validate_tolerance(self):
        """Test validation of convergence tolerance."""
        config = AnalysisConfig(baseline_convergence_tolerance=-1e-6)
        with pytest.raises(ValueError):
            config.validate()
    
    def test_validate_min_T(self):
        """Test validation of baseline minimum T."""
        config = AnalysisConfig(baseline_min_T=50)
        with pytest.raises(ValueError):
            config.validate()
    
    def test_validate_dpi(self):
        """Test validation of plot DPI."""
        config = AnalysisConfig(plot_dpi=10)
        with pytest.raises(ValueError):
            config.validate()
        
        config2 = AnalysisConfig(plot_dpi=2000)
        with pytest.raises(ValueError):
            config2.validate()
    
    def test_model_candidates(self):
        """Test default regression model candidates."""
        config = AnalysisConfig()
        expected = ["additive", "multiplicative", "saturation"]
        assert config.regression_model_candidates == expected


class TestGlobalConfigFunctions:
    """Tests for global configuration functions."""
    
    def test_get_full_config_structure(self):
        """Test that get_full_config returns expected structure."""
        config_dict = get_full_config()
        
        assert "numerical" in config_dict
        assert "simulation" in config_dict
        assert "analysis" in config_dict
        
        assert "rtol" in config_dict["numerical"]
        assert "atol" in config_dict["numerical"]
        assert "sigma" in config_dict["simulation"]
        assert "rho" in config_dict["simulation"]
        assert "baseline_convergence_tolerance" in config_dict["analysis"]
    
    def test_set_simulation_seed(self):
        """Test setting simulation seed."""
        original_seed = simulation_config.seed
        set_simulation_seed(999)
        assert simulation_config.seed == 999
        assert np.random.get_state()[1][0] != 0  # RNG state changed
        # Restore
        set_simulation_seed(original_seed)
    
    def test_set_noise_levels(self):
        """Test setting custom noise levels."""
        original_levels = simulation_config.noise_levels.copy()
        new_levels = [0.01, 0.05, 0.1]
        set_noise_levels(new_levels)
        assert simulation_config.noise_levels == new_levels
        # Restore
        set_noise_levels(original_levels)
    
    def test_set_noise_levels_negative(self):
        """Test that setting negative noise levels raises error."""
        with pytest.raises(ValueError):
            set_noise_levels([0.1, -0.1])
    
    def test_set_N_oscillators(self):
        """Test setting number of oscillators."""
        original_N = simulation_config.N_oscillators
        set_N_oscillators(10)
        assert simulation_config.N_oscillators == 10
        # Restore
        set_N_oscillators(original_N)
    
    def test_set_N_oscillators_zero(self):
        """Test that setting N=0 raises error."""
        with pytest.raises(ValueError):
            set_N_oscillators(0)
    
    def test_set_N_oscillators_adjusts_windows(self):
        """Test that small t_max adjusts window sizes."""
        original_t_max = simulation_config.t_max
        original_dt = simulation_config.dt_output
        
        # Set very short simulation time
        simulation_config.t_max = 0.1
        simulation_config.dt_output = 0.01
        set_N_oscillators(3)  # Should trigger window adjustment
        
        # Window sizes should be reduced or minimum set
        assert all(w <= (0.1 / 0.01) - 10 for w in simulation_config.ftle_window_sizes) or \
               simulation_config.ftle_window_sizes == [100]
        
        # Restore
        simulation_config.t_max = original_t_max
        simulation_config.dt_output = original_dt
        set_N_oscillators(5)  # Restore N

class TestConstants:
    """Tests for module-level constants."""
    
    def test_default_seed_constant(self):
        """Test DEFAULT_SEED matches simulation config seed."""
        from code.config import DEFAULT_SEED
        assert DEFAULT_SEED == simulation_config.seed
    
    def test_default_n_constant(self):
        """Test DEFAULT_N matches simulation config N."""
        from code.config import DEFAULT_N
        assert DEFAULT_N == simulation_config.N_oscillators
    
    def test_default_rtol_constant(self):
        """Test DEFAULT_RTOl matches numerical settings."""
        from code.config import DEFAULT_RTOl
        assert DEFAULT_RTOl == numerical_settings.rtol
    
    def test_default_atol_constant(self):
        """Test DEFAULT_ATOL matches numerical settings."""
        from code.config import DEFAULT_ATOL
        assert DEFAULT_ATOL == numerical_settings.atol
    
    def test_default_noise_levels_constant(self):
        """Test DEFAULT_NOISE_LEVELS matches simulation config."""
        from code.config import DEFAULT_NOISE_LEVELS
        assert DEFAULT_NOISE_LEVELS == simulation_config.noise_levels