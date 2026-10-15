"""
Preprocessing package shim.

This top‑level package re‑exports the actual preprocessing modules located
under ``code/preprocessing`` so that test suites can import them with the
expected ``preprocessing.<module>`` import path.
"""
# Export submodules for convenience
from .data_validation import *  # noqa: F401,F403
