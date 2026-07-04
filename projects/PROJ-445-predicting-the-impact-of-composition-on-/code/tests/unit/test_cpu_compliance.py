"""
Unit tests for CPU compliance utilities.

These tests ensure that the CPU-only compliance mechanisms work correctly
and prevent accidental GPU usage in the pipeline.
"""
import os
import sys
import tempfile
import pytest
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression

# Import the module under test
from src.utils.cpu_compliance import (
    enforce_cpu_mode,
    validate_cpu_only_model,
    limit_memory_usage,
    validate_data_size_for_cpu,
    setup_cpu_environment,
    ensure_no_gpu_operations,
    FORCE_CPU
)

class TestEnforceCpuMode:
    """Tests for CPU mode enforcement."""
    
    def test_sets_cuda_visible_devices(self):
        """Test that CUDA_VISIBLE_DEVICES is set to empty string."""
        enforce_cpu_mode()
        assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    
    def test_sets_omp_threads(self):
        """Test that OMP_NUM_THREADS is set to 2."""
        enforce_cpu_mode()
        assert os.environ.get("OMP_NUM_THREADS") == "2"
    
    def test_sets_mkl_dynamic_false(self):
        """Test that MKL_DYNAMIC is set to FALSE."""
        enforce_cpu_mode()
        assert os.environ.get("MKL_DYNAMIC") == "FALSE"

class TestValidateCpuOnlyModel:
    """Tests for CPU-only model validation."""
    
    def test_linear_regression_cpu_compatible(self):
        """Test that LinearRegression is CPU compatible."""
        model = LinearRegression()
        result = validate_cpu_only_model(model)
        assert result is True
    
    def test_gradient_boosting_cpu_compatible(self):
        """Test that GradientBoostingRegressor is CPU compatible."""
        model = GradientBoostingRegressor()
        result = validate_cpu_only_model(model)
        assert result is True
    
    def test_random_forest_cpu_compatible(self):
        """Test that RandomForestRegressor is CPU compatible."""
        model = RandomForestRegressor(n_estimators=10)
        result = validate_cpu_only_model(model)
        assert result is True
    
    def test_xgboost_cpu_config(self):
        """Test that XGBoost is configured for CPU when available."""
        try:
            from xgboost import XGBRegressor
            model = XGBRegressor()
            result = validate_cpu_only_model(model)
            assert result is True
            # Check that tree_method is set to hist for CPU optimization
            assert model.tree_method == 'hist'
        except ImportError:
            pytest.skip("XGBoost not installed")

class TestLimitMemoryUsage:
    """Tests for memory usage limiting."""
    
    def test_sets_omp_threads(self):
        """Test that OMP_NUM_THREADS is set for memory limiting."""
        limit_memory_usage()
        assert os.environ.get("OMP_NUM_THREADS") == "2"
    
    def test_enables_copy_on_write(self):
        """Test that pandas copy-on-write is enabled."""
        limit_memory_usage()
        assert pd.options.mode.copy_on_write is True

class TestValidateDataSizeForCpu:
    """Tests for data size validation."""
    
    def test_accepts_small_dataset(self):
        """Test that small datasets are accepted."""
        df = pd.DataFrame({'a': range(100), 'b': range(100)})
        result = validate_data_size_for_cpu(df, max_rows=5000)
        assert result is True
    
    def test_rejects_large_dataset(self):
        """Test that large datasets raise RuntimeError."""
        df = pd.DataFrame({'a': range(6000), 'b': range(6000)})
        with pytest.raises(RuntimeError, match="exceeds CPU processing limit"):
            validate_data_size_for_cpu(df, max_rows=5000)
    
    def test_warns_high_dimensionality(self):
        """Test that high dimensionality triggers warning."""
        df = pd.DataFrame(np.random.rand(100, 150))
        # This should not raise, but may log a warning
        result = validate_data_size_for_cpu(df, max_rows=5000)
        assert result is True

class TestSetupCpuEnvironment:
    """Tests for complete CPU environment setup."""
    
    def test_returns_config_dict(self):
        """Test that setup returns a configuration dictionary."""
        config = setup_cpu_environment()
        assert isinstance(config, dict)
        assert 'cpu_only_mode' in config
        assert 'cuda_available' in config
        assert 'num_cpus' in config
        assert 'environment' in config
    
    def test_sets_environment_variables(self):
        """Test that environment variables are properly set."""
        config = setup_cpu_environment()
        assert config['environment']['CUDA_VISIBLE_DEVICES'] == ""
        assert config['environment']['OMP_NUM_THREADS'] == "2"

class TestEnsureNoGpuOperations:
    """Tests for GPU operation prevention."""
    
    def test_linear_model_cpu_safe(self):
        """Test that linear models pass GPU check."""
        model = LinearRegression()
        X = pd.DataFrame({'a': range(10)})
        ensure_no_gpu_operations(model, X)
    
    def test_gradient_boosting_cpu_safe(self):
        """Test that gradient boosting models pass GPU check."""
        model = GradientBoostingRegressor()
        X = pd.DataFrame({'a': range(10)})
        ensure_no_gpu_operations(model, X)
    
    def test_large_data_raises_error(self):
        """Test that large data raises error in GPU check."""
        model = GradientBoostingRegressor()
        X = pd.DataFrame({'a': range(6000)})
        with pytest.raises(RuntimeError, match="exceeds CPU processing limit"):
            ensure_no_gpu_operations(model, X)

class TestForceCpuEnvironmentVariable:
    """Tests for FORCE_CPU_COMPLIANCE environment variable."""
    
    def test_force_cpu_true(self):
        """Test behavior when FORCE_CPU_COMPLIANCE is true."""
        with patch.dict(os.environ, {"FORCE_CPU_COMPLIANCE": "true"}):
            # Re-import to pick up new env var
            import importlib
            import src.utils.cpu_compliance
            importlib.reload(src.utils.cpu_compliance)
            assert src.utils.cpu_compliance.FORCE_CPU is True
    
    def test_force_cpu_false(self):
        """Test behavior when FORCE_CPU_COMPLIANCE is false."""
        with patch.dict(os.environ, {"FORCE_CPU_COMPLIANCE": "false"}):
            import importlib
            import src.utils.cpu_compliance
            importlib.reload(src.utils.cpu_compliance)
            assert src.utils.cpu_compliance.FORCE_CPU is False
    
    def test_force_cpu_missing(self):
        """Test default behavior when FORCE_CPU_COMPLIANCE is not set."""
        # Remove the env var if it exists
        env_copy = os.environ.copy()
        env_copy.pop("FORCE_CPU_COMPLIANCE", None)
        with patch.dict(os.environ, env_copy, clear=False):
            import importlib
            import src.utils.cpu_compliance
            importlib.reload(src.utils.cpu_compliance)
            assert src.utils.cpu_compliance.FORCE_CPU is True  # Default is True
