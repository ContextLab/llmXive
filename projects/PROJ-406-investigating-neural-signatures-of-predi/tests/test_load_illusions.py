"""
Minimal test suite for ``src.ingest.load_illusions``.

The CI verification step runs the module directly
(``python -m src.ingest.load_illusions download_muller``) and checks the
produced files.  This test simply ensures that the public API exists and
can be imported without side‑effects.
"""

import importlib

def test_module_importable():
    mod = importlib.import_module("src.ingest.load_illusions")
    assert hasattr(mod, "download_and_clean")
    assert callable(mod.download_and_clean)

# The heavy‑weight integration test (downloading the real dataset) is performed
# by the task verification script, not by this unit test, to keep CI fast.