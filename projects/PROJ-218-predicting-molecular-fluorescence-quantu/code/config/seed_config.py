"""
Seed configuration module.

Importing this module will:
1. Load seed values from `code/config/seeds.yaml`.
2. Set the environment variable ``PYTHONHASHSEED`` and seed the
   ``random``, ``numpy`` and ``torch`` RNGs accordingly.
3. Write the seed mapping to ``results/seeds.json`` (via
   ``load_and_set_seeds`` from ``code.data.download_raw``).
4. Assert that the runtime seed settings match the values stored in
   ``results/seeds.json`` (via ``assert_seeds_match`` from
   ``utils.seed_assert``).

This guarantees that any downstream stochastic operation sees the same,
reproducible seed configuration, satisfying Constitution Principle I.
"""

from code.data.download_raw import load_and_set_seeds
from utils.seed_assert import assert_seeds_match

# Load seeds from the YAML config, set RNGs, and write results/seeds.json
load_and_set_seeds()

# Verify that the current runtime seed state matches the written JSON
assert_seeds_match()
