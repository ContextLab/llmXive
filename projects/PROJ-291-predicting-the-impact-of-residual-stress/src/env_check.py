"""
src/env_check
---------------
Wrapper that re‑exports the implementation in ``code/src/env_check.py``.
This allows the module to be executed as ``python -m src.env_check``,
matching the expectations of the test suite.
"""
from code.src.env_check import *  # noqa: F401,F403
