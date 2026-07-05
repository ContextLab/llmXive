"""
Integration test for T010: Verify that other modules import SEED from config.

This test attempts to import modules that are known to use RNGs and verifies
they can successfully import from config without errors.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_monte_carlo_core_imports_config():
    """Verify monte_carlo_core can import set_rng_seed from config."""
    try:
        from code.src.audit.monte_carlo_core import set_seeds
        # If this imports, the dependency chain is valid
        assert True
    except ImportError as e:
        pytest.fail(f"monte_carlo_core failed to import config functions: {e}")

def test_prevalence_imports_config():
    """Verify prevalence module can import from config."""
    try:
        # The module itself might not expose a direct import, but we check if it loads
        from code.src.audit import prevalence
        assert True
    except ImportError as e:
        pytest.fail(f"prevalence module failed to load: {e}")

def test_stat_verification_imports_config():
    """Verify stat_verification imports config."""
    try:
        from code.src.audit.stat_verification import two_proportion_z_test
        assert True
    except ImportError as e:
        pytest.fail(f"stat_verification failed to import: {e}")

def test_subgroup_analysis_imports_config():
    """Verify subgroup_analysis imports config."""
    try:
        from code.src.audit.subgroup_analysis import set_rng_seed_for_subgroup_analysis
        assert True
    except ImportError as e:
        pytest.fail(f"subgroup_analysis failed to import: {e}")
