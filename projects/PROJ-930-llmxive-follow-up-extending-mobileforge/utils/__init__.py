"""
Top‑level ``utils`` package shim.

The project's source code lives under ``code/utils``.  To allow imports such as
``import utils.emulator`` (used throughout the test suite) we extend the package
search path of this shim to include that directory.

This file does **not** duplicate any implementation – it merely makes the
existing modules under ``code/utils`` importable as ``utils.<module>``.
"""

import pathlib

# Resolve the sibling ``code/utils`` directory relative to the repository root.
_code_utils_path = pathlib.Path(__file__).parent.parent / "code" / "utils"

# If the directory exists, add it to this package's ``__path__`` so that
# submodule imports (e.g., ``utils.emulator``) are resolved from there.
if _code_utils_path.is_dir():
    __path__.append(str(_code_utils_path))

# Export nothing directly; all symbols are provided by the real modules.