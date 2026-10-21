"""
Wrapper module that re-exports the project's configuration utilities.
The original implementation resides in `code/utils/config.py`. By importing
everything here we maintain a stable public API (`utils.config`) used
throughout the codebase and test suite.
"""
from code.utils.config import *  # noqa: F403,F401
