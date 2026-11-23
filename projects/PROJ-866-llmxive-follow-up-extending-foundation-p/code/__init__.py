"""
llmXive Research Pipeline - Code Package Compatibility Shim
---------------------------------------------------------
This package originally contained all source modules under the ``code/`` directory.
To satisfy the project plan that expects a ``src/`` layout while preserving the
original entry point, we extend the package search path to include the sibling
``src/`` directory.  This allows imports such as ``import code.main`` to resolve
to the original implementation in ``code/main.py`` and also makes modules
available under ``code.<submodule>`` when they exist in ``src/``.

The shim does **not** move any existing files; it merely adds the ``src/``
directory to ``__path__`` so that Python will look there for submodules.
"""

import sys
from pathlib import Path

# Resolve the absolute path to the sibling ``src`` directory.
_src_dir = Path(__file__).resolve().parent / "src"

# If the directory exists, prepend it to the package search path.
if _src_dir.is_dir():
    # ``__path__`` is a list of directory strings that Python searches for
    # submodules of this package.  Adding the ``src`` directory ensures that
    # ``code.<module>`` imports will also find modules placed under ``src/``.
    __path__.insert(0, str(_src_dir))

# Optionally expose a convenience attribute so that external code can
# discover the mirrored source location.
__src_path__ = str(_src_dir)
