"""
Unit test for the seed‑configuration module.

The test imports ``code.config.seed_config`` (which is executed on import)
and then calls ``utils.seed_assert.assert_seeds_match`` to ensure that the
runtime seeds are identical to the values written in ``results/seeds.json``.
"""

import importlib

def test_seed_configuration_matches_results():
    # Import the seed configuration – this will set the seeds and write the JSON
    importlib.import_module("code.config.seed_config")
    # Now import the assertion helper and run it; it should not raise
    from utils.seed_assert import assert_seeds_match

    # The function raises RuntimeError on mismatch; the test passes if no error
    assert_seeds_match()