"""
Tests to verify the package structure and imports are correctly exposed.
"""
import pytest
import sys

def test_package_version():
    import code
    assert hasattr(code, '__version__')
    assert isinstance(code.__version__, str)
    assert code.__version__ == "0.1.0"

def test_submodules_importable():
    import code
    assert hasattr(code, 'data')
    assert hasattr(code, 'analysis')

def test_config_exposed():
    import code
    # Verify all config classes and functions are exposed at the top level
    assert hasattr(code, 'NumericalSettings')
    assert hasattr(code, 'SimulationConfig')
    assert hasattr(code, 'AnalysisConfig')
    assert hasattr(code, 'get_full_config')
    assert hasattr(code, 'set_simulation_seed')
    assert hasattr(code, 'set_noise_levels')
    assert hasattr(code, 'set_N_oscillators')

def test_all_exports():
    import code
    expected_exports = [
        "data",
        "analysis",
        "NumericalSettings",
        "SimulationConfig",
        "AnalysisConfig",
        "get_full_config",
        "set_simulation_seed",
        "set_noise_levels",
        "set_N_oscillators",
    ]
    assert set(code.__all__) == set(expected_exports)