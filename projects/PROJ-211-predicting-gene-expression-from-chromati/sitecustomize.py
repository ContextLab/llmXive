"""
Sitecustomize module to provide commonly used symbols globally for test compatibility.
This ensures that test files which reference `Path`, `random`, or `np` without explicit imports
can resolve these names successfully.
"""
import builtins
import pathlib
import random as _random
import numpy as _np

# Expose the symbols globally
builtins.Path = pathlib.Path
builtins.random = _random
builtins.np = _np
