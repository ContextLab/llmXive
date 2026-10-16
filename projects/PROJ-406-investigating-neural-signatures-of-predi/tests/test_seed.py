"""
Test that the global seed produces deterministic NumPy outputs across
separate invocations of ``set_global_seed``.
"""
import numpy as np

from src.utils.seed import set_global_seed

def test_deterministic_numpy_random():
    # First run: set seed and draw a value
    set_global_seed(42)
    first = np.random.rand()

    # Reset seed to the same value and draw again
    set_global_seed(42)
    second = np.random.rand()

    assert first == second, "NumPy random numbers differ despite identical seed"

def test_package_import_sets_seed():
    """
    Ensure that importing ``src`` (which triggers ``src.__init__``) also
    sets the seed to the default value. We compare the value produced
    after import with the value obtained by explicitly calling the
    helper with the same default.
    """
    import importlib
    import src  # This should have already set the seed to DEFAULT_SEED

    # Capture a value after the package import
    val_after_import = np.random.rand()

    # Reset seed manually to the same default and capture a second value
    from src.utils.seed import DEFAULT_SEED
    set_global_seed(DEFAULT_SEED)
    val_manual = np.random.rand()

    assert val_after_import == val_manual, (
        "Package import did not set the global seed to the default value"
    )