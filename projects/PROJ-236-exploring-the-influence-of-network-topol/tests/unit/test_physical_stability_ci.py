"""
Unit test for the CI verification script ``code/ci/check_physical_stability.py``.

The test uses monkey‑patching to replace the heavy I/O functions with
lightweight mocks, allowing us to verify the exit‑code logic without
requiring real atomic seed files.
"""

import sys
import types
import builtins
import importlib
import pytest

# Import the module under test as a fresh module to allow monkey‑patching.
@pytest.fixture
def ci_module(monkeypatch):
    # Reload the module to ensure a clean state.
    module = importlib.import_module("ci.check_physical_stability")
    importlib.reload(module)

    # Mock ``load_seed_structures`` to return a controllable list.
    def mock_load_seed_structures():
        # Return a list of dummy objects; their content is irrelevant.
        return ["seed1", "seed2", "seed3", "seed4", "seed5", "seed6", "seed7", "seed8", "seed9", "seed10"]

    # Mock ``filter_stable_structures`` to simulate a given pass rate.
    def mock_filter_stable_structures(seeds):
        # Accept the first N seeds; the rest are considered unstable.
        # The test will replace this function to control the pass rate.
        return seeds

    monkeypatch.setattr(module, "load_seed_structures", mock_load_seed_structures)
    monkeypatch.setattr(
        "utils.validation.filter_stable_structures", mock_filter_stable_structures
    )
    return module

def test_ci_passes_when_rejection_rate_below_threshold(monkeypatch, ci_module):
    # Simulate 90 % pass rate (1 rejected out of 10 → 10 % reject, which should fail).
    # To stay below the 5 % threshold we need at most 0 rejected.
    def mock_filter(seeds):
        return seeds  # all pass

    monkeypatch.setattr(
        "utils.validation.filter_stable_structures", mock_filter
    )

    # Capture sys.exit calls.
    with pytest.raises(SystemExit) as excinfo:
        ci_module.main()
    assert excinfo.value.code == 0

def test_ci_fails_when_rejection_rate_exceeds_threshold(monkeypatch, ci_module):
    # Simulate 90 % pass rate (1 rejected out of 10 → 10 % reject) → should fail.
    def mock_filter(seeds):
        # Return only the first 9 seeds as stable.
        return seeds[:-1]

    monkeypatch.setattr(
        "utils.validation.filter_stable_structures", mock_filter
    )

    with pytest.raises(SystemExit) as excinfo:
        ci_module.main()
    assert excinfo.value.code == 1

def test_ci_fails_when_no_seeds_found(monkeypatch, ci_module):
    # Simulate an empty seed list.
    def mock_load():
        return []

    monkeypatch.setattr(ci_module, "load_seed_structures", mock_load)

    with pytest.raises(SystemExit) as excinfo:
        ci_module.main()
    assert excinfo.value.code == 1