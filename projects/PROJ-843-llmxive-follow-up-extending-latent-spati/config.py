"""
Top‑level configuration shim.

The project’s codebase imports configuration utilities directly from a
module named ``config`` (e.g. ``from config import get_raw_dir``).  The
actual implementation lives in ``code/config.py``.  To keep the import
statements unchanged while allowing the implementation to stay under the
``code/`` package, this shim re‑exports everything from ``code.config``.
"""

# Re‑export all public symbols from the real implementation.
# The ``code`` package is on the Python path because the repository’s
# entry‑point scripts prepend the ``code`` directory to ``sys.path``.
# Importing with a star import respects the ``__all__`` definition in
# ``code/config.py`` and therefore only the intended public API is
# exposed.
from code.config import *  # noqa: F403,F401

# Ensure that tools like ``help(config)`` show a useful docstring.
__doc__ = __doc__ + "\n\n" + getattr(__import__("code.config"), "__doc__", "")
