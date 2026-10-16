"""
Top-level data package.

This package re-exports the trajectory generation utilities defined in
``code/data/generator.py`` so that legacy imports (e.g. ``import data.generator``)
continue to work.

The original implementation lives under ``code/data`` and provides the
full functionality required by the unit tests.
"""
# Re-export everything from the implementation module
from .generator import *  # noqa: F401,F403
