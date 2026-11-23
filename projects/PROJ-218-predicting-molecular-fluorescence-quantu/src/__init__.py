"""
Package initialisation for ``src``.
Importing the top‑level ``src`` package automatically imports the
seed‑configuration module, ensuring that seeds are pinned and verified
before any other ``src`` submodule (e.g., preprocessing, training) is
imported.
"""
# Import the seed configuration as a side‑effect.
import code.config.seed_config  # noqa: F401
