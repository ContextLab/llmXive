"""
Generators package for random matrices.
Exposes only the functionality that is actually implemented.
"""

# The only public generator needed by the current pipeline is
# `generate_wigner_matrix`.  Import it from the sibling module
# `wigner.py`.  Previously this __init__ tried to import
# `save_raw_wigner_matrix` and `main`, which do not exist and caused
# an ImportError when `code/main.py` imported the package.

from .wigner import generate_wigner_matrix

__all__ = ["generate_wigner_matrix"]
