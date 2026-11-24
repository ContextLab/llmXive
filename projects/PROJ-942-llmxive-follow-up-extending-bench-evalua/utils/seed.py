"""
Wrapper module that forwards calls to the implementation residing in
``code/utils/seed.py``.

The project’s source code stores the real implementation under the
``code/utils`` package.  Tests and external scripts expect to import
``utils.seed`` directly from the repository root.  This thin wrapper simply
re‑exports the functions from the original module, preserving the public API
without duplicating logic.
"""

# The implementation lives in ``code/utils/seed.py``.  Import it and expose
# the same public names.
from importlib import import_module
import sys
from pathlib import Path

# Ensure the ``code`` directory is on ``sys.path`` so the import works even
# when this wrapper is imported before any other project code has adjusted the
# path (e.g., during the test suite execution).
_code_dir = Path(__file__).resolve().parents[1] / "code"
if str(_code_dir) not in sys.path:
    sys.path.insert(0, str(_code_dir))

_impl = import_module("utils.seed")  # actually loads ``code/utils/seed.py``

# Re‑export the public symbols expected by the test suite.
set_seeds = _impl.set_seeds
get_seed_state_summary = _impl.get_seed_state_summary
DEFAULT_SEED = _impl.DEFAULT_SEED

__all__ = ["set_seeds", "get_seed_state_summary", "DEFAULT_SEED"]