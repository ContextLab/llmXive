"""
Site customization to ensure that project modules located in the `code/` directory
are importable without needing to modify the PYTHONPATH manually.

This file is automatically imported by Python at interpreter startup if it is
found on the import path. By adding the absolute path of the `code/` directory
to `sys.path`, imports such as `import numpy_real` (which resolves to
`code/numpy_real.py`) succeed even when scripts are executed from the repository
root.
"""

import os
import sys

# Determine the absolute path to the `code` directory relative to this file.
_code_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "code"))

# Insert the `code` directory at the front of sys.path if it's not already there.
if _code_dir not in sys.path:
    sys.path.insert(0, _code_dir)

# Clean up temporary variables.
del os, sys, _code_dir
