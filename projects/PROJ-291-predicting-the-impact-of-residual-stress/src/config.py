"""
src/config.py
---------------
Wrapper module that re‑exports the global configuration constants defined in
``code/src/config.py``. This makes ``src.config`` importable as expected by the
quick‑start commands and the test suite.
"""

# Re‑export all names (SEED, PROXY_COEFFICIENTS, etc.)
from code.src.config import *  # noqa: F401,F403
