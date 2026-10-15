"""
Utility package initializer for the project.

This module re-exports the public I/O helper functions so that
``import code.utils`` provides direct access to the most commonly
used utilities without requiring the caller to know the exact sub‑module
layout.

The original implementation attempted to import ``compute_md5`` and
``verify_md5`` which are not defined in ``code.utils.io`` and caused
import errors throughout the code‑base.  The corrected version simply
re‑exports everything that ``code.utils.io`` defines (including the
checksum helpers that actually exist – e.g. ``compute_sha256`` and
``verify_sha256``) as well as ``load_parquet`` and ``save_parquet``.
"""

# Re‑export all public symbols from the I/O helper module.
# Using a wildcard import is safe here because ``io.py`` defines only the
# intended public utilities; any private names (prefixed with an underscore)
# are not imported into the package namespace.
from .io import *  # noqa: F401,F403

__all__ = [name for name in globals() if not name.startswith('_')]
