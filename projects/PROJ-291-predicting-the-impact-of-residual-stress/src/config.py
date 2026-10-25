"""
src/config
------------
Wrapper that re‑exports the central configuration defined in
``code/src/config.py``.  Importing ``src.config`` provides the same
constants required by downstream modules and the test suite.
"""
from code.src.config import *  # noqa: F401,F403