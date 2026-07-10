"""
Smoke test to verify all project modules and dependencies can be imported.
"""
import pytest
import sys

def test_dependencies_installed():
    """Verify core dependencies are installed."""
    required = [
        'pandas', 'numpy', 'scikit-learn', 'scipy',
        'matplotlib', 'requests', 'pyyaml', 'statsmodels'
    ]
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            pytest.fail(f"Dependency {pkg} is not installed.")

def test_utils_config_import():
    """Test utils.config module imports."""
    from utils.config import os  # Config imports os, but we test the module load
    # Actually, utils.config only imports os, let's test the module itself
    import utils.config
    assert hasattr(utils.config, 'os')

def test_utils_logging_import():
    """Test utils.logging module imports."""
    from utils.logging import setup_logger
    assert callable(setup_logger)

def test_verify_checksums_import():
    """Test utils.verify_checksums module imports."""
    from utils.verify_checksums import calculate_md5, verify_checksums
    assert callable(calculate_md5)
    assert callable(verify_checksums)

def test_data_models_import():
    """Test data.models module imports."""
    from data.models import CosmicRayFlux, SolarActivityIndex, CompositionRatio
    assert CosmicRayFlux is not None
    assert SolarActivityIndex is not None
    assert CompositionRatio is not None
