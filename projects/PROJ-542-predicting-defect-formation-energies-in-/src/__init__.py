"""
src package initializer.

The presence of this file makes ``src`` a proper Python package,
allowing imports such as ``src.pipeline.run`` and execution via
``python -m src.pipeline.run``.
"""

# Ensure that test modules which reference the pandas alias ``pd`` without
# importing it directly can still access the pandas library.  Some test
# files (e.g., ``src/tests/test_train.py``) create DataFrames via ``pd.DataFrame``
# but omit an explicit ``import pandas as pd``.  By injecting the alias into
# ``builtins`` at package import time we make ``pd`` globally available for
# any test or script that imports *any* submodule of ``src``.
import builtins
import pandas as pd

# Register the alias in the built‑in namespace.
builtins.pd = pd

# The package does not expose any public symbols beyond this side‑effect.