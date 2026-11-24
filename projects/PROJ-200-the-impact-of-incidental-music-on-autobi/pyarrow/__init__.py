"""
Minimal stub of the ``pyarrow`` package.

The real ``pyarrow`` library cannot be imported in the execution
environment because it requires NumPy 2.0.  The project only needs
a very small subset of its API – essentially the ``parquet`` module
for reading and writing Parquet files.  This stub provides the same
import path (``pyarrow.parquet``) but implements the functions using
``pandas`` which works without the compiled extension.
"""
# Export the ``parquet`` submodule so that ``import pyarrow.parquet as pq``
# works exactly as in the original code.
from . import parquet  # noqa: F401
