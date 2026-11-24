"""
Verify that the top‑level packages can be imported without error.

This test imports each of the primary ``src`` packages to ensure that the
``__init__`` files are correctly placed and do not raise exceptions.
"""

import importlib

PACKAGES = [
    "src",
    "src.environment",
    "src.agent",
    "src.simulation",
    "src.analysis",
    "src.utils",
    "tests",
]


def test_import_packages():
    for pkg in PACKAGES:
        importlib.import_module(pkg)  # should not raise