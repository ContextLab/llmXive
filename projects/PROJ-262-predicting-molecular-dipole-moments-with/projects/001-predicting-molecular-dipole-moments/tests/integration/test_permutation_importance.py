"""
Integration test for the permutation importance pipeline.

The test verifies that the ``compute_permutation_importance`` function can
be executed on a small synthetic dataset without exceeding the memory
budget of 8 GB.  It also checks that the returned importance array has the
expected shape.
"""

import tracemalloc

import numpy as np
from sklearn.ensemble import RandomForestRegressor

# Import the function under test.  The ``code`` directory is added to
# ``PYTHONPATH`` by the test runner, so we can import directly from the
# ``attribution`` package.
from attribution.permutation_importance import compute_permutation_importance


def test_permutation_importance_memory_profile() -> None:
    """
    Train a tiny Random Forest on synthetic data and compute permutation
    importance while profiling memory usage.

    The test asserts:
    * The importance vector has length equal to the number of features.
    * Peak memory consumption stays well below the 8 GB limit.
    """
    # Synthetic dataset: 100 samples, 5 features.
    rng = np.random.default_rng(seed=42)
    X = rng.random((100, 5))
    y = rng.random(100)

    # Fit a minimal Random Forest model.
    model = RandomForestRegressor(
        n_estimators=10,
        max_depth=3,
        random_state=0,
    )
    model.fit(X, y)

    # Start memory tracing.
    tracemalloc.start()
    importances = compute_permutation_importance(
        model=model,
        X=X,
        y=y,
        metric="neg_mean_absolute_error",
        n_repeats=5,
        random_state=0,
    )
    # Capture peak memory usage (in bytes).
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Basic sanity checks.
    assert importances.shape == (X.shape[1],), (
        f"Expected importance vector of length {X.shape[1]}, got {importances.shape}"
    )
    # 8 GB = 8 * 1024³ bytes.
    assert peak_bytes < 8 * 1024 ** 3, (
        f"Memory usage exceeded 8 GB: {peak_bytes / (1024 ** 3):.2f} GB"
    )