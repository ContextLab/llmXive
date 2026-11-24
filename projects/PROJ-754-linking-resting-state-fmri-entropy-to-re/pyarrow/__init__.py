"""
Minimal stub for the `pyarrow` package.

The execution environment ships a broken `pyarrow` installation that
lacks the ``__version__`` attribute, causing import failures when
pandas attempts to import it.  Providing a lightweight stub with the
expected attribute resolves the issue without pulling in the full
dependency (which is unnecessary for this project because we use
``fastparquet`` for parquet I/O).

Only the ``__version__`` attribute is required for pandas' internal
checks, so we define it here.  If other ``pyarrow`` symbols are
accessed they will raise ``ImportError`` – this is acceptable because
the codebase never relies on them.
"""
__version__ = "0.0.0"
