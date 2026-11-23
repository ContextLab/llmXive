"""
PROJ-257: Statistical Properties of Simulated Black Hole Mergers
"""

# Make the ``src`` package a namespace package that spans both the
# top‑level ``src`` directory and the duplicate ``code/src`` directory.
# This resolves import collisions where modules import ``src`` and expect
# to find sub‑packages such as ``src.data`` that live in the top‑level
# ``src`` tree.

import os
import pkgutil

# Extend the package path to include any other directories named ``src``
# that are part of the same project (e.g., the sibling top‑level ``src``).
__path__ = pkgutil.extend_path(__path__, __name__)  # type: ignore

# Add the sibling top‑level ``src`` directory if it exists.
sibling_src = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
if os.path.isdir(sibling_src) and sibling_src not in __path__:
    __path__.append(sibling_src)
