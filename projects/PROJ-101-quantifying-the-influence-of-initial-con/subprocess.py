"""
Compatibility shim for the standard library ``subprocess`` module.

The project previously contained a top‑level ``subprocess.py`` that
shadowed the real standard‑library module, causing import errors
(e.g. missing ``PIPE``).  This file re‑exports the original
implementation so that any ``import subprocess`` performed by the
test suite or third‑party libraries resolves to the correct module.
"""
import importlib
import sys

# Load the genuine stdlib subprocess module.
_std_subprocess = importlib.import_module('subprocess')

# Populate the current module's globals with everything from the real module.
globals().update(_std_subprocess.__dict__)

# Ensure the module appears as ``subprocess`` in ``sys.modules``.
sys.modules[__name__] = _std_subprocess
