"""
Package initialisation for the ``analysis`` sub‑module.

The original ``__init__`` attempted to import a large number of symbols
using ``from .exploratory import ( ... )``.  Several of those symbols no
longer exist (or the imported modules rely on the old ``log_operation``
signature).  Importing them here caused the entire ``analysis`` package to
fail during import, which in turn broke every script that performed
``from analysis.xxx import …``.

To restore stability we limit the public imports to the modules that are
actually used by the pipeline.  Individual scripts import the functions they
need directly, so keeping the ``__all__`` list small is safe and avoids
circular‑import problems.
"""

# Export the most frequently used public helpers.
from .complexity_visualization import KnotRecord, generate_complexity_visualization_examples
from .save_crossing_braid_plot import create_crossing_vs_braid_plot
from .complexity_visualization_runner import main as run_complexity_visualization

__all__ = [
    "KnotRecord",
    "generate_complexity_visualization_examples",
    "create_crossing_vs_braid_plot",
    "run_complexity_visualization",
]
